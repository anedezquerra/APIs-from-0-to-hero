"""Stdlib + asyncio load harness for offline API load testing.

Implements both classic workload models against an in-process ASGI app:

* open model   -- requests are scheduled at a fixed rate (requests/sec),
                  independent of how fast responses come back;
* closed model -- a fixed number of workers each run request-response
                  loops (think: a fixed pool of users).

Includes a bucketed latency histogram with percentile estimation, a
saturation sweep that prints a knee-point table, and a Little's Law
cross-check (L = lambda * W) for the closed model.

Latency numbers are *illustrative* (they depend on your machine); the
harness never asserts on wall-clock values.

Run the demo:  python load_harness.py
"""
from __future__ import annotations

import asyncio
import bisect
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from fastapi import FastAPI

BOUNDS_MS: tuple[int, ...] = (1, 2, 5, 10, 25, 50, 100, 250, 500, 1_000, 2_500, 5_000)


@dataclass
class Histogram:
    """Fixed-bucket latency histogram; percentiles read the bucket ceiling."""

    bounds: tuple[int, ...] = BOUNDS_MS
    counts: list[int] = field(init=False)
    errors: int = 0
    total_ms: float = 0.0

    def __post_init__(self) -> None:
        self.counts = [0] * (len(self.bounds) + 1)

    def record_ms(self, ms: float) -> None:
        self.counts[bisect.bisect_right(self.bounds, ms)] += 1
        self.total_ms += ms

    @property
    def total(self) -> int:
        return sum(self.counts)

    def percentile_ms(self, p: float) -> float:
        if self.total == 0:
            return 0.0
        rank = max(1, int(p / 100.0 * self.total + 0.999999))
        seen = 0
        for i, count in enumerate(self.counts):
            seen += count
            if seen >= rank:
                return float(self.bounds[i]) if i < len(self.bounds) else float("inf")
        return float("inf")

    def mean_ms(self) -> float:
        return self.total_ms / self.total if self.total else 0.0


async def _send(client: httpx.AsyncClient, hist: Histogram, path: str) -> None:
    started = time.perf_counter()
    try:
        resp = await client.get(path)
        await resp.aread()
        if resp.status_code >= 500:
            hist.errors += 1
    except (httpx.HTTPError, OSError):
        hist.errors += 1
    finally:
        hist.record_ms((time.perf_counter() - started) * 1_000.0)


async def open_loop(
    client: httpx.AsyncClient, *, rps: float, duration_s: float, path: str = "/work"
) -> Histogram:
    """Open model: schedule sends at fixed virtual offsets from the start."""
    hist = Histogram()
    period = 1.0 / rps
    start = time.perf_counter()
    tasks: list[asyncio.Task[None]] = []
    k = 0
    while k * period < duration_s:  # deterministic scheduled count
        scheduled = start + k * period
        delay = scheduled - time.perf_counter()
        if delay > 0:
            await asyncio.sleep(delay)
        tasks.append(asyncio.create_task(_send(client, hist, path)))
        k += 1
    if tasks:
        await asyncio.gather(*tasks)
    return hist


async def closed_loop(
    client: httpx.AsyncClient, *, workers: int, duration_s: float, path: str = "/work"
) -> Histogram:
    """Closed model: each worker issues the next request only after the
    previous response arrives."""
    hist = Histogram()
    deadline = time.perf_counter() + duration_s

    async def worker() -> None:
        while time.perf_counter() < deadline:
            await _send(client, hist, path)

    await asyncio.gather(*(worker() for _ in range(workers)))
    return hist


def create_workload_app(*, work_ms: int = 20, max_concurrent: int = 4) -> FastAPI:
    """Demo workload: simulated async work behind a concurrency semaphore,
    so the service has a real, findable saturation point."""
    app = FastAPI(title="Load harness demo workload")
    semaphore = asyncio.Semaphore(max_concurrent)

    @app.get("/work")
    async def work() -> dict[str, str]:
        async with semaphore:
            await asyncio.sleep(work_ms / 1_000.0)
        return {"status": "ok"}

    return app


@dataclass
class SweepRow:
    rps: int
    completed: int
    p50_ms: float
    p99_ms: float
    error_rate: float
    is_knee: bool


async def saturation_sweep(
    app: Any,
    levels: tuple[int, ...] = (25, 50, 100, 150, 200, 300, 400),
    duration_s: float = 0.3,
) -> list[SweepRow]:
    """Ramp offered RPS; flag the knee: first level where p99 explodes
    (10x baseline) or errors appear."""
    rows: list[SweepRow] = []
    baseline_p50: float | None = None
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://load.test"
    ) as client:
        for rps in levels:
            hist = await open_loop(client, rps=rps, duration_s=duration_s)
            p50 = hist.percentile_ms(50)
            p99 = hist.percentile_ms(99)
            error_rate = hist.errors / hist.total if hist.total else 1.0
            if baseline_p50 is None:
                baseline_p50 = p50 if p50 > 0 else 1.0
            is_knee = (p99 > 10.0 * baseline_p50) or error_rate > 0.0
            rows.append(SweepRow(rps, hist.total, p50, p99, error_rate, is_knee))
    return rows


def render_sweep(rows: list[SweepRow]) -> str:
    lines = ["  rps | completed |  p50 ms |   p99 ms | err % | knee",
             "------+-----------+---------+----------+-------+-----"]
    for row in rows:
        lines.append(
            f"{row.rps:5} | {row.completed:9} | {row.p50_ms:7.0f} | "
            f"{row.p99_ms:8.0f} | {100 * row.error_rate:5.1f} | "
            f"{'<< KNEE' if row.is_knee else ''}"
        )
    return "\n".join(lines)


async def littles_law_check(workers: int = 8, duration_s: float = 0.5) -> str:
    """Closed model: verify L = lambda * W against the configured concurrency."""
    app = create_workload_app(work_ms=20, max_concurrent=10_000)  # unthrottled
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://load.test"
    ) as client:
        hist = await closed_loop(client, workers=workers, duration_s=duration_s)
    lam = hist.total / duration_s            # throughput lambda (requests/s)
    w = hist.mean_ms() / 1_000.0             # mean residence time W (s)
    l_est = lam * w
    return (
        f"closed model: workers={workers} throughput={lam:.0f} req/s "
        f"mean={hist.mean_ms():.1f} ms -> L = lambda*W = {l_est:.1f} "
        f"(configured concurrency: {workers})"
    )


async def _demo() -> None:
    print("saturation sweep (illustrative numbers, machine-dependent):")
    rows = await saturation_sweep(create_workload_app())
    print(render_sweep(rows))
    print(await littles_law_check())


if __name__ == "__main__":
    asyncio.run(_demo())
