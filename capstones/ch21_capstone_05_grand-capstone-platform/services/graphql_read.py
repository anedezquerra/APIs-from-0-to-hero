"""GraphQL read model (M2): /graphql over catalog + telemetry projections.

TODO: depth <= 5, persisted queries only; reads never expose uncommitted
state (projection fed by the orders outbox event stream).
"""

from __future__ import annotations


def create_app() -> "object":
    """Build the GraphQL read-model app. TODO: implement per M2 exit criteria."""
    raise NotImplementedError("TODO: implement graphql read model")
