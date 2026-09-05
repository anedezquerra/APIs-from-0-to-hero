"""Capstone 19.5 [staff] — Quality-Gate Architecture for a Fleet.

Executable scaffolding for the gate design: defect-class catchers, CI budget,
broker topology, flake policy, and rollout plan. See README.md.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class DefectClass(str, Enum):
    CONTRACT_BREAK = "contract-break"
    REGRESSION = "regression"
    SCHEMA_DRIFT = "schema-drift"
    CAPACITY_REGRESSION = "capacity-regression"
    SECURITY_REGRESSION = "security-regression"
    FLAKE = "flake"


@dataclass(frozen=True)
class Catcher:
    """The single cheapest gate that owns a defect class."""

    defect: DefectClass
    gate: str               # e.g. "unit", "contract", "property", "load-sweep"
    pyramid_layer: str
    budget_s: int


@dataclass(frozen=True)
class GateBudget:
    """Per-PR CI budget; must fit four minutes with written justifications."""

    total_budget_s: int = 240
    allocations: tuple[tuple[str, int], ...] = ()
    justifications: tuple[str, ...] = ()


def assign_catchers() -> list[Catcher]:
    """Every defect class gets exactly one designated cheapest catcher."""
    raise NotImplementedError("TODO: implement assign_catchers")


def budget_gates(catchers: list[Catcher]) -> GateBudget:
    """Fit the per-PR budget; deep sweeps and soaks move to scheduled jobs."""
    raise NotImplementedError("TODO: implement budget_gates")


def broker_topology() -> dict[str, str]:
    """Pact storage, version tagging, can-i-deploy semantics per environment."""
    raise NotImplementedError("TODO: implement broker_topology")


def flake_policy() -> dict[str, str]:
    """Quarantine SLA, deletion rule, dashboards."""
    raise NotImplementedError("TODO: implement flake_policy")


def rollout_plan() -> list[str]:
    """Advisory-to-blocking rollout with measurable adoption metrics and a
    self-check requirement for every gate."""
    raise NotImplementedError("TODO: implement rollout_plan")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fleet-gates", description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("DRY RUN: outline = catchers -> budget -> broker -> flake policy -> rollout")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
