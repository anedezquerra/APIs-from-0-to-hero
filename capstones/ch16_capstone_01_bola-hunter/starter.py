"""Capstone 16.1 [junior] — BOLA Hunter.

A notes API with a deliberately missing ownership check, an exploit script,
and the fix. Synthetic lab tokens only. See README.md for the contract.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class Note:
    id: int
    owner: str
    body: str


@dataclass(frozen=True)
class LabUser:
    """Synthetic lab identity — unsigned lab tokens acceptable here."""

    username: str
    token: str


def seed_store() -> dict[int, Note]:
    """20 synthetic notes owned by 4 fictional users (deterministic)."""
    raise NotImplementedError("TODO: implement seed_store")


def create_app(store: dict[int, Note], *, hardened: bool) -> "object":
    """Build the FastAPI notes API.

    TODO: ``GET/PATCH /notes/{id}``. When ``hardened`` is False the GET
    ownership check is deliberately missing (the vulnerability); when True,
    a Guard-style object check returns 403 on every cross-owner access.
    """
    raise NotImplementedError("TODO: implement create_app")


def exploit(client: "object", attacker: LabUser, ids: range = range(1, 21)) -> list[Note]:
    """Enumerate note ids with one user's credential and dump every note.

    Contract: against the vulnerable build this retrieves foreign notes;
    against the hardened build every request is denied (403).
    """
    raise NotImplementedError("TODO: implement exploit")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bola-hunter", description=__doc__)
    parser.add_argument("--hardened", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        mode = "hardened" if args.hardened else "vulnerable"
        print(f"DRY RUN: run exploit.py against the {mode} build")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
