"""Capstone 19.2 [mid] — Property Suite for a New Resource.

Bring /warehouses under property-based and fuzz coverage; plant two bugs and
watch the suite find and shrink them. See README.md for the contract.
"""

from __future__ import annotations

import argparse
from typing import Sequence

from pydantic import BaseModel, Field


class WarehouseCreate(BaseModel):
    """TODO: constrain fields — code pattern, non-empty city, capacity >= 0."""

    code: str = Field(pattern=r"^WH-[A-Z]{3}$")
    city: str = Field(min_length=1, max_length=80)
    capacity_m2: int = Field(ge=0)


class WarehouseRead(BaseModel):
    id: int
    code: str
    city: str
    capacity_m2: int


def create_app(*, plant_bug: str | None = None) -> "object":
    """The registry app extended with /warehouses and RFC 9457 errors.

    TODO: ``plant_bug="500"`` installs the 500 trigger;
    ``plant_bug="bad201"`` installs the schema-violating 201. Both must be
    found and shrunk by the property suite.
    """
    raise NotImplementedError("TODO: implement create_app")


def hostile_payloads() -> "object":
    """The Hypothesis strategy encoding the three universal invariants.

    TODO: strategy over hostile WarehouseCreate payloads; the tests assert
    zero 5xx, schema-valid responses, and problem-shaped 4xx. Suites run
    with ``derandomize=True`` so they pass repeatably.
    """
    raise NotImplementedError("TODO: implement hostile_payloads")


def fuzz_candidates(seed: int = 42, n: int = 200) -> list[dict]:
    """Fuzzer candidate generation for the new fields (seeded)."""
    raise NotImplementedError("TODO: implement fuzz_candidates")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="property-warehouses", description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("DRY RUN: property suite + fuzz campaign over /warehouses")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
