"""Capstone 18.5 [staff] — Incident Program in a Box.

SLOs, runbooks, a scripted retry-storm game day, and a blameless postmortem
— all reproducible from seeds. See README.md for the contract.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"


@dataclass(frozen=True)
class Slo:
    """One service's SLO set with per-endpoint thresholds."""

    service: str
    availability_target: float
    latency_p99_ms: float
    freshness_max_lag_s: float


@dataclass
class GameDayResult:
    detection_s: float = 0.0
    mitigation_s: float = 0.0
    resolution_s: float = 0.0


def define_slos() -> list[Slo]:
    """SLOs for the three platform services."""
    raise NotImplementedError("TODO: implement define_slos")


def generate_runbook(slo: Slo) -> str:
    """Runbook for one service with every placeholder filled.

    Contract: runbooks cite the SLOs and dashboards they belong to.
    """
    raise NotImplementedError("TODO: implement generate_runbook")


def script_retry_storm(seed: int = 42) -> list[tuple[float, str, float]]:
    """The case-study incident as a simulator timeline (t_s, metric, value).

    Contract: a spans-per-trace alert fires before the latency burn pages.
    """
    raise NotImplementedError("TODO: implement script_retry_storm")


def run_game_day(timeline: list[tuple[float, str, float]], seed: int) -> GameDayResult:
    """Two roles — injector and runbook-follower — with measured timings.

    Contract: deterministic from the seed; a second run reproduces the
    timelines within one minute of simulated time.
    """
    raise NotImplementedError("TODO: implement run_game_day")


def postmortem(result: GameDayResult) -> str:
    """Blameless postmortem from the generator.

    Contract: includes a "lessons for the SLO" section whose action items
    name at least one alerting-topology change with an owner.
    """
    raise NotImplementedError("TODO: implement postmortem")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="incident-program", description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("DRY RUN: SLOs -> runbooks -> retry-storm game day -> postmortem")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
