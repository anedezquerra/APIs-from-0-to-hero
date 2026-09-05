"""Capstone 19.4 [senior] — Capacity Report from a Knee Sweep.

Predict capacity analytically, measure it with open-model sweeps, and
cross-check with Little's Law. See README.md for the contract.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Sequence


def predict_capacity_rps(max_concurrent: int, work_ms: float) -> float:
    """Analytic prediction: c / S."""
    raise NotImplementedError("TODO: implement predict_capacity_rps")


@dataclass
class SweepPoint:
    offered_rps: float
    p50_ms: float = 0.0
    p99_ms: float = 0.0
    error_rate: float = 0.0


@dataclass
class KneeResult:
    work_ms: float
    knee_rps: float = 0.0
    points: list[SweepPoint] = field(default_factory=list)


def open_model_sweep(work_ms: float, *, seed: int = 42) -> KneeResult:
    """Open-model sweep at one work_ms setting; tabulate the knee.

    TODO: deterministic simulation (seeded); no wall-clock assertions —
    numbers are illustrative and labeled as such.
    """
    raise NotImplementedError("TODO: implement open_model_sweep")


def closed_model_check(work_ms: float, clients: int, *, seed: int = 42) -> dict[str, float]:
    """Closed-model cross-check: verify L = lambda * W."""
    raise NotImplementedError("TODO: implement closed_model_check")


def capacity_report(results: list[KneeResult], closed: dict[str, float]) -> str:
    """The one-page report: knee table, Little's Law cross-check, headroom
    recommendation, and the CI perf budget.

    Contract: predicted and measured knees compared with the discrepancy
    explained (factor-of-two bar).
    """
    raise NotImplementedError("TODO: implement capacity_report")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="knee-sweep", description=__doc__)
    parser.add_argument("--work-ms", type=float, nargs=3, default=[5.0, 20.0, 80.0])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print(f"DRY RUN: knee sweep at work_ms={list(args.work_ms)}")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
