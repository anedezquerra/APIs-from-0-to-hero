"""Telemetry service (M3): /v1/telemetry/stream SSE surface.

TODO: operator dashboard feed with Last-Event-ID resume; trace context
propagated end to end (M4).
Backed by ..\..\..\datasets\northwind_robotics\telemetry_events.jsonl.
"""

from __future__ import annotations


def create_app() -> "object":
    """Build the telemetry SSE app. TODO: implement per M3 exit criteria."""
    raise NotImplementedError("TODO: implement telemetry service")
