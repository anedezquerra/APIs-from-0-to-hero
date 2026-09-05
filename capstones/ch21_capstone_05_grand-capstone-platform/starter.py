"""Capstone 21.5 [staff] — The Grand Capstone: Northwind Robotics API Platform.

Milestone runner CLI for the four-milestone delivery plan (M1 REST core,
M2 read model + internal RPC, M3 async platform, M4 production hardening).
See README.md for the full specification.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"
SERVICES_DIR = Path(__file__).resolve().parent / "services"
SPECS_DIR = Path(__file__).resolve().parent / "specs"


@dataclass(frozen=True)
class Milestone:
    number: int
    theme: str
    exit_criteria: str


MILESTONES: tuple[Milestone, ...] = (
    Milestone(1, "REST core",
              "catalog + orders green on contract tests; RFC 9457; keyset "
              "pagination; idempotency replay test passing"),
    Milestone(2, "Read model + internal RPC",
              "GraphQL read model with depth limiting; inventory gRPC with "
              "streaming WatchStock; gateway auth + rate tiers"),
    Milestone(3, "Async platform",
              "outbox relay, signed webhooks with delivery log and replay, "
              "SSE telemetry; AsyncAPI specs linted in CI"),
    Milestone(4, "Production hardening",
              "OTel traces across surfaces; SLO dashboards; conformance gate; "
              "load and failure-mode evidence; portal published"),
)


def milestone_status(number: int) -> dict[str, str]:
    """Report which artifacts for milestone ``number`` exist vs. are TODO.

    TODO: map each milestone to its service modules, spec artifacts, and
    tests; report present/missing per artifact so the exit criteria are
    mechanically checkable.
    """
    raise NotImplementedError("TODO: implement milestone_status")


def run_chaos_drill(*, seed: int = 42) -> bool:
    """Kill inventory mid-order; verify designed circuit-breaker behavior and
    zero data loss (outbox replay verified). Deterministic from the seed."""
    raise NotImplementedError("TODO: implement run_chaos_drill")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="grand-capstone", description=__doc__)
    parser.add_argument("--milestone", type=int, choices=[1, 2, 3, 4], default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    milestone = MILESTONES[args.milestone - 1]
    if args.dry_run:
        print(f"DRY RUN: M{milestone.number} {milestone.theme}")
        print(f"exit criteria: {milestone.exit_criteria}")
        return 0
    print("Scaffold ready. Implement services/, specs/, and tests/ per README.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
