"""Capstone 16.4 [senior] — Threat-Model Pipeline.

STRIDE worksheets as a build artifact: generated from OpenAPI, completed by
humans, enforced by a --check CI gate. See README.md for the contract.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

WORKSHEETS_DIR = Path(__file__).resolve().parent / "worksheets"


@dataclass(frozen=True)
class StrideRow:
    """One STRIDE row for one endpoint."""

    category: str   # S | T | R | I | D | E
    threat: str
    mitigation: str


@dataclass
class Worksheet:
    endpoint: str
    rows: list[StrideRow] = field(default_factory=list)
    completed: bool = False


def generate_skeletons(openapi: dict) -> list[Worksheet]:
    """Generate one skeleton worksheet per endpoint.

    TODO: heuristics flag query-string filters (I), file uploads (T), and
    webhook registrations (S/R) — at least three heuristics, each unit
    tested.
    """
    raise NotImplementedError("TODO: implement generate_skeletons")


def load_committed(directory: Path = WORKSHEETS_DIR) -> list[Worksheet]:
    """Load the human-completed worksheets checked into the repo."""
    raise NotImplementedError("TODO: implement load_committed")


def check(openapi: dict, directory: Path = WORKSHEETS_DIR) -> list[str]:
    """CI gate: diff generated skeletons against committed worksheets.

    Returns the list of violations (undocumented or unmodeled endpoints);
    empty means the gate is green. Output ordering deterministic.
    """
    raise NotImplementedError("TODO: implement check")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="threat-model-gate", description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="Exit nonzero when worksheets are stale or missing.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("DRY RUN: generate skeletons and diff against committed worksheets")
        return 0
    if args.check:
        try:
            violations = check({})
        except NotImplementedError:
            print("Scaffold ready. Implement the TODO items in starter.py to begin.")
            return 0
        for v in violations:
            print(f"VIOLATION: {v}")
        return 1 if violations else 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
