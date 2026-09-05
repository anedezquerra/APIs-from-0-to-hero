"""Capstone 14.5 [staff] — Rate-Limiting Architecture for Northwind at 100k rps.

Executable scaffolding for the design document: endpoint tiers, topology
choices, runbook coverage, and the cost model. See README.md.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Sequence

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"


class Tier(str, Enum):
    EXACTNESS_REQUIRED = "exactness-required"
    APPROXIMATE_FAIR = "approximate-fair"
    SHEDDING_ONLY = "shedding-only"


class Topology(str, Enum):
    GLOBAL_CELL = "global-cell"
    REGIONAL = "regional"
    LOCAL_PLUS_SYNC = "local-plus-sync"


@dataclass(frozen=True)
class EndpointPlan:
    """One endpoint's protection plan. ``limit_derivation`` must show the math."""

    path: str
    cost_class: str          # read | write | export | admin
    tier: Tier
    topology: Topology
    fail_policy: str         # "fail-open" | "fail-closed"
    limit_per_minute: int
    limit_derivation: str    # the numeric derivation — no round numbers from nowhere


def author_endpoint_inventory() -> list[dict]:
    """40 synthetic endpoints across read/write/export/admin with cost weights."""
    raise NotImplementedError("TODO: implement author_endpoint_inventory")


def classify(inventory: list[dict]) -> list[EndpointPlan]:
    """Assign tier, topology, failure policy, and a derived limit per endpoint.

    Contract: every endpoint gets all four fields; approximate tiers carry a
    stated over-admission bound.
    """
    raise NotImplementedError("TODO: implement classify")


def cost_model(plans: list[EndpointPlan], *, tenants: int = 2000,
               target_rps: int = 100_000) -> dict[str, float]:
    """Redis cell sizing from key cardinality and N; reject-cheaply egress cost.

    Contract: reports limiter infrastructure as a fraction of serving cost
    at 10^5 rps; the design doc must show it under 2% or explain why not.
    """
    raise NotImplementedError("TODO: implement cost_model")


def runbook() -> dict[str, dict[str, str]]:
    """The three named incidents with detection signals and rollback steps.

    Keys: ``limiter-cell-outage``, ``abusive-tenant-drill``,
    ``capacity-brownout``. Each maps to detection/rollback/fail-policy.
    """
    raise NotImplementedError("TODO: implement runbook")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rl-architecture", description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("DRY RUN: outline = tiers -> topologies -> header contract -> runbook -> cost model -> red team")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
