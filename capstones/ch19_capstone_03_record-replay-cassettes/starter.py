"""Capstone 19.3 [mid] — Record–Replay Cassette Library.

A minimal VCR for httpx: record, sanitize, replay, and detect stale
cassettes. See README.md for the contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

CASSETTE_PATH = Path(__file__).resolve().parent / "cassettes" / "robot_registry.json"

Sanitizer = Callable[[dict], dict]


@dataclass(frozen=True)
class RecordedResponse:
    status: int
    headers: dict[str, str]
    body: str


def request_key(method: str, path: str, body: bytes = b"") -> str:
    """The cassette lookup key.

    TODO: method+path (+ canonical body hash in strict mode).
    """
    raise NotImplementedError("TODO: implement request_key")


def default_sanitizer(exchange: dict) -> dict:
    """Strip credential-like material before anything touches disk.

    Contract: no Authorization header, no cookie, no token-shaped value
    survives sanitization.
    """
    raise NotImplementedError("TODO: implement default_sanitizer")


class RecordingTransport:  # TODO: subclass httpx.BaseTransport
    """Wrap a live transport; write each exchange to the cassette."""

    def __init__(self, inner: "object", cassette: Path, sanitizer: Sanitizer) -> None:
        raise NotImplementedError("TODO: implement RecordingTransport")


class ReplayingTransport:  # TODO: subclass httpx.BaseTransport
    """Serve exchanges from the cassette — the app can be absent entirely."""

    def __init__(self, cassette: Path, *, strict: bool = True) -> None:
        raise NotImplementedError("TODO: implement ReplayingTransport")


def freshness_check(cassette: Path, *, max_age_days: int = 30,
                    expected_hash: str | None = None) -> bool:
    """Detect a stale cassette by recorded date or content hash.

    TODO: replay alone cannot detect app drift — this check is the
    compensating control.
    """
    raise NotImplementedError("TODO: implement freshness_check")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cassette-vcr", description=__doc__)
    parser.add_argument("--mode", choices=["record", "replay"], default="replay")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print(f"DRY RUN: {args.mode} via {CASSETTE_PATH}")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
