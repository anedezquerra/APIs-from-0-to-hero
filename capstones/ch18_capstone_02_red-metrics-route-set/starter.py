"""Capstone 18.2 [mid] — RED Metrics for a Real Route Set.

Per-endpoint rate/errors/duration over four routes with an exactly-enforced
cardinality bound. See README.md for the contract.
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"

ROUTES = ("POST /fleet/telemetry", "GET /fleet/status", "GET /fleet/{id}", "GET /health")
STATUS_CLASSES = ("2xx", "4xx", "5xx")


@dataclass(frozen=True)
class SyntheticRequest:
    route: str
    latency_ms: float
    status_class: str


def generate_traffic(n: int = 2000, seed: int = 42) -> list[SyntheticRequest]:
    """Seeded traffic: per-route latency model, 0.2% error rate on one route."""
    raise NotImplementedError("TODO: implement generate_traffic")


@dataclass
class RedMetrics:
    """Counter + histogram per (route, status_class). Nothing else — the
    cardinality bound is the point: exported series == routes x classes."""

    counts: dict[tuple[str, str], int] = field(default_factory=dict)
    buckets: dict[tuple[str, str], list[float]] = field(default_factory=dict)

    def record(self, request: SyntheticRequest) -> None:
        raise NotImplementedError("TODO: implement RedMetrics.record")

    def series_count(self) -> int:
        """Exported series count; asserted equal to len(ROUTES) x len(STATUS_CLASSES)."""
        raise NotImplementedError("TODO: implement RedMetrics.series_count")

    def render_table(self) -> str:
        """Per-route rate, error ratio, p50/p99 from bucket counts (deterministic)."""
        raise NotImplementedError("TODO: implement RedMetrics.render_table")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="red-metrics", description=__doc__)
    parser.add_argument("--requests", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print(f"DRY RUN: {args.requests} seeded requests across {len(ROUTES)} routes")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
