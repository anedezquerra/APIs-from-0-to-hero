"""Capstone 6.5 [staff] — OpenAPI-First Generator Round-Trip.

Author the spec, implement against it, and gate CI on contract divergence.
See README.md for the contract.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Sequence

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"
SPEC_PATH = Path(__file__).resolve().parent / "orders.openapi.yaml"


class ChangeClass(str, Enum):
    COMPATIBLE = "compatible"
    BREAKING = "breaking"


@dataclass(frozen=True)
class SpecDiff:
    """One difference between the pinned spec and the running schema."""

    location: str            # JSON-path-ish location of the difference
    classification: ChangeClass
    reason: str              # human-readable, actionable


def load_pinned_spec(path: Path = SPEC_PATH) -> dict:
    """Parse the authored OpenAPI 3.1 document.

    TODO: parse YAML (or keep the pinned copy as JSON to stay stdlib-only);
    fail with an actionable error when required top-level blocks
    (``servers``, ``components``, ``securitySchemes``) are missing.
    """
    raise NotImplementedError("TODO: implement load_pinned_spec")


def diff_specs(pinned: dict, generated: dict) -> list[SpecDiff]:
    """Classify every difference between pinned and generated schemas.

    TODO: additions of optional fields are COMPATIBLE; removed/renamed
    fields, removed paths, and tightened requirements are BREAKING; output
    ordering must be deterministic (sorted by location).
    """
    raise NotImplementedError("TODO: implement diff_specs")


def gate(pinned_path: Path = SPEC_PATH) -> int:
    """CI gate: fetch /openapi.json from the running app and diff.

    Returns 0 when the diff is empty or only compatible; 1 on any breaking
    difference, printing the human-readable reasons.
    """
    raise NotImplementedError("TODO: implement gate")


def create_app() -> "object":
    """The FastAPI implementation generated/implemented from the spec."""
    raise NotImplementedError("TODO: implement create_app")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openapi-gate", description=__doc__)
    parser.add_argument("--spec", type=Path, default=SPEC_PATH)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print(f"DRY RUN: diff running /openapi.json against {args.spec}")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
