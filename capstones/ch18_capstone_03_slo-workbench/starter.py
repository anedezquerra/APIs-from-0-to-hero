"""Capstone 18.3 [mid] — SLO Workbench.

A burn-rate policy design tool evaluated against three scripted incidents.
See README.md for the contract.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Iterator, Sequence


@dataclass(frozen=True)
class ErrorSample:
    """One evaluation instant: error ratio over the trailing window."""

    t_s: float
    error_ratio: float


@dataclass(frozen=True)
class PolicyRow:
    """One burn-rate alert row: short/long window pair and threshold."""

    burn_rate: float
    short_window_s: float
    long_window_s: float


@dataclass
class AlertTimeline:
    pages: list[float] = field(default_factory=list)   # t_s of each page
    false_positives: int = 0

    def time_to_page_s(self) -> float | None:
        raise NotImplementedError("TODO: implement AlertTimeline.time_to_page_s")


def incident_total_outage(seed: int = 1) -> Iterator[ErrorSample]:
    """A 3-minute total outage."""
    raise NotImplementedError("TODO: implement incident_total_outage")


def incident_error_bleed(seed: int = 2) -> Iterator[ErrorSample]:
    """A 6-hour 2% error bleed."""
    raise NotImplementedError("TODO: implement incident_error_bleed")


def incident_flapping(seed: int = 3) -> Iterator[ErrorSample]:
    """30 seconds on / 30 seconds off — the reset-and-refire adversary."""
    raise NotImplementedError("TODO: implement incident_flapping")


def stock_policy() -> list[PolicyRow]:
    """The chapter's stock burn-rate table."""
    raise NotImplementedError("TODO: implement stock_policy")


def evaluate(policy: list[PolicyRow], samples: list[ErrorSample]) -> AlertTimeline:
    """Run a policy table over an incident timeline (pure, deterministic)."""
    raise NotImplementedError("TODO: implement evaluate")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="slo-workbench", description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("DRY RUN: stock policy vs 3 incidents (outage, bleed, flapping)")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
