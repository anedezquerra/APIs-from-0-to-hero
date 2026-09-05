"""Capstone 10.1 [junior] — Idempotency-Key Client SDK.

One key per logical operation, replayed across retries, exactly one
server-side mutation. See README.md for the contract.
"""

from __future__ import annotations

import argparse
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"

MAX_ATTEMPTS = 5


class PayloadConflictError(Exception):
    """422: same key, different payload — surfaced to the caller, never retried."""


@dataclass(frozen=True)
class Attempt:
    number: int
    outcome: str  # "success" | "retryable" | "conflict" | "failed"


@dataclass
class Operation:
    """One logical operation. The key is minted once, at construction.

    TODO: ``key`` must be a UUIDv4 generated exactly once per Operation;
    two Operations over identical payloads must have different keys.
    """

    payload: dict
    key: str = field(default_factory=lambda: str(uuid.uuid4()))
    attempts: list[Attempt] = field(default_factory=list)


class IdempotentClient:
    """httpx wrapper speaking the idempotency-key protocol."""

    def __init__(self, client: "object") -> None:
        self._client = client

    def submit(self, op: Operation) -> dict:
        """Submit with bounded retry.

        TODO: retry on connection error and 409 (honor Retry-After), never
        on 422; every attempt appended to ``op.attempts`` with number and
        outcome; raise :class:`PayloadConflictError` on a 422 conflict.
        """
        raise NotImplementedError("TODO: implement IdempotentClient.submit")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="idempotency-sdk", description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print(f"DRY RUN: submit one transfer operation to {args.base_url}")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
