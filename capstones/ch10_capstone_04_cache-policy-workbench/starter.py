"""Capstone 10.4 [senior] — Cache-Policy Workbench.

Rank candidate cache policies over a scripted traffic timeline by origin
load, staleness window, and error resilience. See README.md for the contract.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"


@dataclass(frozen=True)
class CachePolicy:
    """One candidate policy, parsed from a Cache-Control-style directive."""

    name: str
    max_age_s: int = 0
    stale_while_revalidate_s: int = 0
    stale_if_error_s: int = 0
    no_store: bool = False
    private: bool = False


@dataclass(frozen=True)
class TimelineEvent:
    """One event in the scripted timeline (arrival | mutation | outage)."""

    t_s: float
    kind: str
    detail: dict = field(default_factory=dict)


@dataclass
class PolicyResult:
    origin_fetches: int = 0
    bytes_saved: int = 0
    longest_stale_serve_s: float = 0.0
    failed_during_outage: int = 0


def load_fixture(path: Path) -> tuple[list[TimelineEvent], list[CachePolicy]]:
    """Load the timeline and candidate policies from a JSON fixture."""
    raise NotImplementedError("TODO: implement load_fixture")


def simulate(policy: CachePolicy, timeline: list[TimelineEvent]) -> PolicyResult:
    """Replay one timeline against one policy.

    TODO: pure function of (policy, timeline) — same inputs, bit-identical
    result. Serve from cache within max-age; extend via
    stale-while-revalidate / stale-if-error as the directives allow.
    """
    raise NotImplementedError("TODO: implement simulate")


def compare(results: dict[str, PolicyResult]) -> str:
    """Render the comparison table deterministically (stable row ordering)."""
    raise NotImplementedError("TODO: implement compare")


def recommend(results: dict[str, PolicyResult]) -> dict[str, str]:
    """Choose a policy per surface (product page, pricing API, account page).

    Contract: the account page must map to ``no-store`` or ``private``;
    every choice carries a one-sentence justification.
    """
    raise NotImplementedError("TODO: implement recommend")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cache-workbench", description=__doc__)
    parser.add_argument("--fixture", type=Path, default=Path("timeline.json"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print(f"DRY RUN: simulate policies over {args.fixture}")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
