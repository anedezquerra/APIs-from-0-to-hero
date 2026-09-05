"""Capstone 6.4 [senior] — Async Migration of a Blocking Service.

Migrate a deliberately blocking service to correct-concurrency form, proving
each step with loop-lag middleware and a concurrency benchmark. See README.md.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, Sequence

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"


@dataclass
class BenchResult:
    """One benchmark run over N concurrent requests."""

    concurrency: int
    p50_ms: float = 0.0
    p99_ms: float = 0.0
    max_loop_lag_ms: float = 0.0
    samples: list[float] = field(default_factory=list)


class OrderRepository(Protocol):
    """The seam that must stay identical across blocking and async variants."""

    def get_order(self, order_id: int) -> dict | None: ...
    def list_orders(self) -> list[dict]: ...


class BlockingSqliteOrderRepository:
    """The baseline bug: synchronous sqlite plus simulated latency.

    TODO: implement with sqlite3 and a configurable ``time.sleep`` delay so
    the loop-lag middleware can prove the blocking baseline.
    """

    def __init__(self, db_path: Path, simulated_latency_s: float = 0.05) -> None:
        raise NotImplementedError("TODO: implement BlockingSqliteOrderRepository")


class AsyncOrderRepository:
    """Variant B: same protocol, blocking work offloaded via asyncio.to_thread."""

    def __init__(self, inner: BlockingSqliteOrderRepository) -> None:
        raise NotImplementedError("TODO: implement AsyncOrderRepository")


def loop_lag_middleware(app: "object") -> "object":
    """Middleware measuring event-loop lag per request.

    TODO: schedule a tight timer tick and record the observed lag; expose
    max lag for the benchmark harness.
    """
    raise NotImplementedError("TODO: implement loop_lag_middleware")


def create_app(repository: OrderRepository, *, variant: str = "baseline") -> "object":
    """Build the app in one of three variants: baseline / def / to_thread."""
    raise NotImplementedError("TODO: implement create_app")


async def run_benchmark(app: "object", concurrency: int = 200) -> BenchResult:
    """Issue ``concurrency`` concurrent requests through ASGITransport.

    TODO: deterministic — seeded dataset, recorded samples, no wall-clock
    assertions in tests (the report carries the numbers).
    """
    raise NotImplementedError("TODO: implement run_benchmark")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="async-migration", description=__doc__)
    parser.add_argument("--variant", choices=["baseline", "def", "to_thread"],
                        default="baseline")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print(f"DRY RUN: benchmark variant={args.variant} at 200-way concurrency.")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
