"""Capstone 21.4 [senior] — Webhook Notification Pipeline with Outbox Replay.

Outbox relay, HMAC-signed webhooks, delivery log with replay, AsyncAPI docs,
and an SSE fallback stream. Synthetic signing secrets only. See README.md.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"

# Synthetic lab secret — never a real credential.
LAB_SIGNING_SECRET = b"nwr-lab-secret-do-not-use"


@dataclass(frozen=True)
class WebhookEvent:
    id: str
    topic: str            # order.created | order.shipped
    payload: dict


@dataclass
class DeliveryRecord:
    event_id: str
    attempts: int = 0
    last_error: str | None = None
    delivered: bool = False


def sign(event: WebhookEvent, secret: bytes = LAB_SIGNING_SECRET) -> str:
    """HMAC signature over the canonical event payload."""
    raise NotImplementedError("TODO: implement sign")


def verify_signature(event: WebhookEvent, signature: str, *, timestamp: float,
                     now: float, window_s: float = 300.0) -> None:
    """Receiver-side verification.

    TODO: reject bad signatures with a 401 problem and stale timestamps
    (outside the window, replay defense) with a 422 problem.
    """
    raise NotImplementedError("TODO: implement verify_signature")


class OutboxRelay:
    """Polling relay with exponential backoff over the outbox table.

    TODO: deliver pending events to the partner endpoint; persist a
    DeliveryRecord per event (attempts, last_error, delivered); no event is
    lost across a simulated broker/receiver outage.
    """

    def __init__(self, client: "object") -> None:
        self._client = client

    def relay_once(self, pending: list[WebhookEvent]) -> list[DeliveryRecord]:
        raise NotImplementedError("TODO: implement OutboxRelay.relay_once")


def replay(event_id: str, log: list[DeliveryRecord]) -> WebhookEvent:
    """Re-send exactly the logged event payload for ``event_id``."""
    raise NotImplementedError("TODO: implement replay")


def create_receiver_app() -> "object":
    """The synthetic partner endpoint: signature + timestamp verification."""
    raise NotImplementedError("TODO: implement create_receiver_app")


def create_sender_app() -> "object":
    """Exposes POST /v1/webhooks/{id}/replay and the SSE fallback stream."""
    raise NotImplementedError("TODO: implement create_sender_app")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="webhook-pipeline", description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("DRY RUN: outbox -> signed webhook -> receiver -> replay + SSE fallback")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
