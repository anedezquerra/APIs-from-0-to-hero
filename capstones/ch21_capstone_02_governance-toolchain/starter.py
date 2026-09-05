"""Capstone 21.2 [mid] — Governance Toolchain.

A team-grade lint gate over OpenAPI/AsyncAPI specs: new rules, JSON report,
--fix-hints, changed-only CI mode. See README.md for the contract.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence


@dataclass(frozen=True)
class Violation:
    """One rule violation. ``rule`` is a stable code (e.g. ``O-007``)."""

    rule: str
    location: str
    message: str
    fix_hint: str = ""


Rule = Callable[[dict, Path], list[Violation]]


def rule_operation_id_camel_case(spec: dict, path: Path) -> list[Violation]:
    """New rule: every operation has an operationId matching camelCase."""
    raise NotImplementedError("TODO: implement rule_operation_id_camel_case")


def rule_error_schemas_in_components(spec: dict, path: Path) -> list[Violation]:
    """New rule: error schemas are registered in components, not inlined."""
    raise NotImplementedError("TODO: implement rule_error_schemas_in_components")


def rule_asyncapi_channel_names(spec: dict, path: Path) -> list[Violation]:
    """New rule: AsyncAPI channel names follow domain.noun.verb."""
    raise NotImplementedError("TODO: implement rule_asyncapi_channel_names")


RULES: list[Rule] = []  # TODO: original five families + the three new rules


def lint_folder(folder: Path) -> list[Violation]:
    """Lint every spec in a folder; deterministic ordering (sorted output)."""
    raise NotImplementedError("TODO: implement lint_folder")


def to_json_report(violations: list[Violation]) -> str:
    """Machine-readable report; parses and round-trips deterministically."""
    raise NotImplementedError("TODO: implement to_json_report")


def check_changed_only(baseline: Path, candidate: Path) -> list[Violation]:
    """CI mode: violations in changed specs only.

    Contract: pre-existing violations in untouched files are ignored; any
    violation in a changed spec fails the build (nonzero exit in main).
    """
    raise NotImplementedError("TODO: implement check_changed_only")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="conformance-gate", description=__doc__)
    parser.add_argument("--baseline", type=Path, default=None)
    parser.add_argument("--candidate", type=Path, default=None)
    parser.add_argument("--fix-hints", action="store_true")
    parser.add_argument("--json", action="store_true", help="Emit the JSON report.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("DRY RUN: lint candidate folder (changed-only when baseline given)")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
