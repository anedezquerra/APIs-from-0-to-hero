"""Capstone 2.5 [staff] — Async Concurrent Fetcher with Bounded Concurrency.

Drain a 10,000-item work queue from the stub at maximum throughput without
tripping the rate limit, exhausting the pool, or losing backpressure.
See README.md for the contract and the required design memo.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"


@dataclass(frozen=True)
class FetcherConfig:
    """Every knob here must be defended in the design memo."""

    max_concurrency: int = 20       # sized by Little's law vs. rate limit
    rate_limit_per_s: float = 45.0  # below the published 50 req/s
    pool_max_connections: int = 20  # aligned to the semaphore
    max_attempts: int = 5
    max_elapsed_s: float = 30.0


@dataclass
class FetchReport:
    completed: int = 0
    failed: int = 0
    retries_429: int = 0
    partial_manifest: list[str] = field(default_factory=list)


class AsyncTokenBucket:
    """Process-wide bucket shared by all fetch tasks.

    TODO: ``acquire`` awaits (via the injected async sleep) until a token is
    available; on a 429 the *whole* fetcher backs off, not one task.
    """

    def __init__(self, rate_per_s: float) -> None:
        self.rate_per_s = rate_per_s

    async def acquire(self) -> None:
        raise NotImplementedError("TODO: implement AsyncTokenBucket.acquire")

    def on_rate_limited(self, retry_after_s: float | None) -> None:
        raise NotImplementedError("TODO: global backoff signal")


class ConcurrentFetcher:
    """Bounded-concurrency drainer.

    TODO: worker tasks pull item ids from an asyncio.Queue; an
    asyncio.Semaphore bounds in-flight requests; httpx pool limits match;
    cancellation drains in-flight work, closes streams, and records a
    partial-results manifest.
    """

    def __init__(self, config: FetcherConfig, client: "object") -> None:
        self.config = config
        self.client = client

    async def drain(self, item_ids: list[str]) -> FetchReport:
        raise NotImplementedError("TODO: implement ConcurrentFetcher.drain")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="async-fetcher", description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--queue-size", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        cfg = FetcherConfig()
        print(f"DRY RUN: drain {args.queue_size} items, config={cfg}")
        return 0
    print("Scaffold ready. Implement the TODO classes in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
