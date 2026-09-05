"""Orders service (M1 + M3): /v1/orders REST surface plus outbox relay.

TODO: idempotency keys on placement; order + outbox atomicity; signed
webhooks (order.created, order.shipped) with delivery log and replay.
Backed by ..\..\..\datasets\northwind_robotics\orders.csv.
"""

from __future__ import annotations


def create_app() -> "object":
    """Build the orders FastAPI app. TODO: implement per M1/M3 exit criteria."""
    raise NotImplementedError("TODO: implement orders service")
