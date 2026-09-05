"""Capstone 19.1 [junior] — A Second Consumer.

Extend the robot-registry contract suite with a billing-service consumer and
watch usage-based verification catch (or ignore) a rename. See README.md.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

PACTS_DIR = Path(__file__).resolve().parent / "pacts"


@dataclass(frozen=True)
class Interaction:
    """One consumer-recorded request/response pair."""

    description: str
    provider_state: str
    method: str
    path: str
    expected_status: int
    expected_fields: tuple[str, ...]    # the fields this consumer actually reads


@dataclass
class Pact:
    consumer: str
    provider: str = "robot-registry"
    interactions: list[Interaction] = field(default_factory=list)

    def write(self, directory: Path = PACTS_DIR) -> Path:
        """Persist the pact deterministically (stable field ordering)."""
        raise NotImplementedError("TODO: implement Pact.write")


def billing_service_pact() -> Pact:
    """The new consumer: reads only ``id`` and ``price_cents`` from GET /robots/{id}.

    Provider state: "a robot with id 11 exists".
    """
    raise NotImplementedError("TODO: implement billing_service_pact")


def verify(pact: Pact, client: "object") -> list[str]:
    """Verify one pact against the app; return failures with JSONPath locations.

    Contract: usage-based — only fields the consumer reads are checked;
    renaming an unread field fails nothing, renaming a read field fails
    exactly the pact that reads it.
    """
    raise NotImplementedError("TODO: implement verify")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="second-consumer", description=__doc__)
    parser.add_argument("--breaking", action="store_true",
                        help="Verify against create_app(breaking=True).")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("DRY RUN: record billing-service pact and verify both pacts")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
