"""Capstone 10.3 [mid] — Optimistic-Locking Order Service.

Reserve and release stock as conditional writes guarded by If-Match, with a
read-decide-write-retry client. See README.md for the contract.
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"

MAX_ATTEMPTS = 10


class PreconditionRequired(Exception):
    """428: the write was blind — an If-Match validator is required."""


class PreconditionFailed(Exception):
    """412: the write was stale — re-read and retry the whole loop."""


@dataclass(frozen=True)
class StockView:
    """What a client read: current quantity plus its validator."""

    sku: str
    quantity: int
    etag: str


@dataclass
class ContentionReport:
    attempts_histogram: dict[int, int] = field(default_factory=dict)
    stale_writes_per_sku: dict[str, int] = field(default_factory=dict)

    def to_text(self) -> str:
        """Deterministic rendering — identical across runs over the same seed."""
        raise NotImplementedError("TODO: implement ContentionReport.to_text")


class ReservationClient:
    """Read-decide-write-retry against the ETag-guarded stock service."""

    def __init__(self, client: "object", rng: random.Random) -> None:
        self._client = client
        self._rng = rng

    def read(self, sku: str) -> StockView:
        raise NotImplementedError("TODO: implement read")

    def reserve(self, sku: str, quantity: int) -> StockView:
        """One full optimistic loop.

        TODO: read, decide, conditional write with If-Match; on 412 re-read
        and retry with seeded jitter, bounded by MAX_ATTEMPTS; blind writes
        must surface :class:`PreconditionRequired` (428).
        """
        raise NotImplementedError("TODO: implement reserve")


def run_order_script(client: ReservationClient, skus: list[str], workers: int,
                     seed: int) -> ContentionReport:
    """Drive ``workers`` concurrent order workers from a seeded script.

    Contract: conservation holds exactly — final quantity equals initial
    minus the sum of accepted reservations.
    """
    raise NotImplementedError("TODO: implement run_order_script")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="optimistic-orders", description=__doc__)
    parser.add_argument("--workers", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print(f"DRY RUN: {args.workers} seeded order workers")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
