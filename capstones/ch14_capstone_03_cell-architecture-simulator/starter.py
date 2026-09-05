"""Capstone 14.3 [mid] — Cell Architecture Simulator.

Quantify the over-admission of cell-based limiting across global, local,
and sync-reconciled topologies. See README.md for the contract.
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class Arrival:
    """One request arrival in the seeded timeline."""

    t_s: float
    key: str


def generate_timeline(keys: int = 10, duration_s: float = 60.0, *,
                      adversarial_key: str = "k00", seed: int = 42) -> list[Arrival]:
    """Seeded Poisson-ish arrivals for ``keys`` keys plus one adversarial key.

    Contract: same seed, identical timeline; the adversarial key bursts at
    window boundaries to maximize over-admission.
    """
    raise NotImplementedError("TODO: implement generate_timeline")


@dataclass
class TopologyResult:
    worst_case_admissions: dict[str, int] = field(default_factory=dict)


def simulate_global(timeline: list[Arrival], limit: int, window_s: float) -> TopologyResult:
    """One exact global limiter. Contract: never exceeds the limit."""
    raise NotImplementedError("TODO: implement simulate_global")


def simulate_local_no_sync(timeline: list[Arrival], limit: int, window_s: float,
                           cells: int = 4) -> TopologyResult:
    """R local limiters at limit/R with no sync.

    Contract: worst-case overshoot matches the R-times prediction.
    """
    raise NotImplementedError("TODO: implement simulate_local_no_sync")


def simulate_local_with_sync(timeline: list[Arrival], limit: int, window_s: float,
                             cells: int = 4, sync_delta_s: float = 1.0) -> TopologyResult:
    """R local limiters reconciled every ``sync_delta_s`` seconds.

    Contract: admissions <= N + R * r * delta at every delta (reconciliation
    subtracts observed remote consumption).
    """
    raise NotImplementedError("TODO: implement simulate_local_with_sync")


def sweep(timeline: list[Arrival], deltas: Sequence[float] = (0.1, 0.5, 1.0, 5.0)) -> str:
    """Produce the pgfplots-ready over-admission table (deterministic rows)."""
    raise NotImplementedError("TODO: implement sweep")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cell-sim", description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("DRY RUN: sweep delta in {0.1, 0.5, 1.0, 5.0} s over the seeded timeline")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
