"""Capstone 21.3 [senior] — Multi-Protocol Read/Write Split.

REST writes, GraphQL reads, gRPC-shaped internal coordination over one
shared store, with a proven consistency test. See README.md.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, Sequence

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"


class Broker(Protocol):
    """Broker-shaped interface; the in-process fake implements this."""

    def publish(self, topic: str, event: dict) -> None: ...
    def poll(self, topic: str) -> list[dict]: ...


class Outbox:
    """Transactional outbox on the write side.

    TODO: order + outbox row commit atomically; the relay publishes pending
    rows to the broker exactly once per row.
    """

    def enqueue(self, event: dict) -> None:
        raise NotImplementedError("TODO: implement Outbox.enqueue")

    def relay(self, broker: Broker) -> int:
        raise NotImplementedError("TODO: implement Outbox.relay")


class InventoryStub:
    """In-process stand-in for the gRPC inventory service.

    TODO: mirror the Reserve/Release contract you write in inventory.proto;
    offline stub acceptable — keep the interface protobuf-shaped.
    """

    def reserve(self, sku: str, quantity: int) -> bool:
        raise NotImplementedError("TODO: implement InventoryStub.reserve")

    def release(self, sku: str, quantity: int) -> None:
        raise NotImplementedError("TODO: implement InventoryStub.release")


def create_write_app(outbox: Outbox, inventory: InventoryStub) -> "object":
    """REST write service.

    TODO: RFC 9457 errors; idempotency keys honored on order placement.
    """
    raise NotImplementedError("TODO: implement create_write_app")


def create_read_app(broker: Broker) -> "object":
    """GraphQL read service over projections.

    TODO: reads never expose uncommitted state; the projection converges
    within a bounded number of polls.
    """
    raise NotImplementedError("TODO: implement create_read_app")


def consistency_check(*, runs: int = 100, seed: int = 42) -> bool:
    """Concurrent orders never oversell stock; the read model converges.

    Contract: deterministic — passes in 100 seeded runs.
    """
    raise NotImplementedError("TODO: implement consistency_check")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="read-write-split", description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("DRY RUN: REST writes -> outbox -> GraphQL reads, 100 seeded runs")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
