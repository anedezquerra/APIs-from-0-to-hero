"""Capstone 18.4 [senior] — Queue Propagation End to End.

One trace across HTTP and a message broker: injection, CONSUMER spans,
span links for batches, and a detectably orphaned legacy consumer.
See README.md for the contract.
"""

from __future__ import annotations

import argparse
import uuid
from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class SpanContext:
    trace_id: str
    span_id: str


@dataclass
class Span:
    name: str
    context: SpanContext
    parent: SpanContext | None = None
    kind: str = "INTERNAL"       # SERVER | PRODUCER | CONSUMER
    links: list[SpanContext] = field(default_factory=list)


@dataclass(frozen=True)
class Message:
    body: bytes
    metadata: dict[str, str]    # traceparent / tracestate live here


class FakeBroker:
    """In-process broker: dict of queues; no network; deterministic.

    TODO: ``publish(queue, message)`` / ``consume(queue)`` preserving FIFO
    order; metadata passes through untouched (that is the point).
    """

    def __init__(self) -> None:
        raise NotImplementedError("TODO: implement FakeBroker")


def inject(context: SpanContext, metadata: dict[str, str]) -> None:
    """Write traceparent/tracestate into message metadata."""
    raise NotImplementedError("TODO: implement inject")


def extract(metadata: dict[str, str]) -> SpanContext | None:
    """Read context back; None when metadata is missing or dropped."""
    raise NotImplementedError("TODO: implement extract")


def consumer_span(message: Message) -> Span:
    """A CONSUMER span parented to the extracted context."""
    raise NotImplementedError("TODO: implement consumer_span")


def batch_consumer_span(messages: list[Message]) -> Span:
    """One span for a 50-message batch: links, not a false single parent."""
    raise NotImplementedError("TODO: implement batch_consumer_span")


def legacy_consumer_span(message: Message) -> Span:
    """A consumer that drops unknown metadata: the orphaned-span failure mode.

    The test must detect the orphan programmatically and log a warning.
    """
    raise NotImplementedError("TODO: implement legacy_consumer_span")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="queue-propagation", description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("DRY RUN: publish -> consume -> batch -> legacy-orphan scenario")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
