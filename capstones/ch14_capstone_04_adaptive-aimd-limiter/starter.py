"""Capstone 14.4 [senior] — Adaptive Limits with AIMD.

An AIMD-adaptive per-tenant limiter tracking a moving capacity signal.
See README.md for the contract.
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field
from typing import Sequence


def capacity_at(t_s: float, seed: int = 42) -> float:
    """Seeded capacity signal oscillating between 150 and 450 rps.

    Contract: pure function of (t_s, seed) — reproducible everywhere.
    """
    raise NotImplementedError("TODO: implement capacity_at")


@dataclass
class AimdController:
    """Additive-increase / multiplicative-decrease per-tenant limiter.

    TODO: evaluate once per second — ``limit += a`` when healthy,
    ``limit *= beta`` on overload — never below ``floor``.
    """

    a: float = 10.0
    beta: float = 0.5
    floor: float = 50.0
    limit: float = 100.0

    def evaluate(self, *, overloaded: bool) -> float:
        """One evaluation step; returns the new limit."""
        raise NotImplementedError("TODO: implement AimdController.evaluate")


@dataclass
class GridCell:
    a: float
    beta: float
    time_to_first_contact_s: float = 0.0
    oscillation_amplitude: float = 0.0
    total_rejected: int = 0


def run_grid(a_values: Sequence[float], beta_values: Sequence[float],
             seed: int = 42) -> list[GridCell]:
    """Simulate each (a, beta) pair against the capacity signal."""
    raise NotImplementedError("TODO: implement run_grid")


def find_knee(cells: list[GridCell]) -> GridCell:
    """Fastest ``a`` whose beta-paired oscillation never exceeds capacity by >10%."""
    raise NotImplementedError("TODO: implement find_knee")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aimd-limiter", description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("DRY RUN: sweep the (a, beta) grid and find the knee")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
