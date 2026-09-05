"""Capstone 18.1 [junior] — Trace Context Conformance Pack.

Extend the chapter's traceparent parser into a conformance checker over a
hand-written corpus. See README.md for the contract.
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

CORPUS_PATH = Path(__file__).resolve().parent / "traceparent_corpus.txt"


@dataclass(frozen=True)
class TraceContext:
    """A parsed W3C traceparent."""

    version: int
    trace_id: str
    parent_id: str
    flags: int


@dataclass(frozen=True)
class CorpusCase:
    header: str
    expect_valid: bool


def parse_traceparent(header: str) -> TraceContext:
    """The chapter's parser, extended.

    TODO: strict v00 parsing; forward-compatible v01 parsing (trailing
    fields tolerated); every rejection raises ``ValueError`` naming the
    offending field — and nothing but ``ValueError``.
    """
    raise NotImplementedError("TODO: implement parse_traceparent")


def format_traceparent(ctx: TraceContext) -> str:
    """Serialize a context back to the wire format (round-trip target)."""
    raise NotImplementedError("TODO: implement format_traceparent")


def load_corpus(path: Path = CORPUS_PATH) -> list[CorpusCase]:
    """One header per line with an expected verdict."""
    raise NotImplementedError("TODO: implement load_corpus")


def check_corpus(cases: list[CorpusCase]) -> list[str]:
    """Run every case through the parser; return per-case failures.

    Contract: empty list means all 25 corpus cases produced the expected
    verdict.
    """
    raise NotImplementedError("TODO: implement check_corpus")


def roundtrip_property(seed: int = 42, n: int = 500) -> int:
    """Seeded round-trip property: parse(header(x)) == x for n contexts.

    Returns the number of passing cases (must equal ``n``).
    """
    raise NotImplementedError("TODO: implement roundtrip_property")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trace-conformance", description=__doc__)
    parser.add_argument("--corpus", type=Path, default=CORPUS_PATH)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print(f"DRY RUN: check {args.corpus} + 500-case round-trip property")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
