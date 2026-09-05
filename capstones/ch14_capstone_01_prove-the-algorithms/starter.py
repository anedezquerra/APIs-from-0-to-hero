"""Capstone 14.1 [junior] — Prove the Algorithms.

Reimplement the five limiters from their mathematical definitions, port the
chapter's 14 tests unmodified, then break each on purpose. See README.md.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class Decision:
    """The shared limiter contract — keep this shape exactly."""

    allowed: bool
    remaining: int
    reset_after_s: float
    retry_after_s: float | None


class Limiter(Protocol):
    """All five algorithms answer the same question at time ``now``."""

    def check(self, key: str, now: float) -> Decision: ...


class FixedWindowLimiter:
    """TODO: N admissions per window of W seconds; derive from the definition.

    Note the known edge: a burst straddling a window boundary can admit 2N.
    """

    def __init__(self, limit: int, window_s: float) -> None:
        raise NotImplementedError("TODO: implement FixedWindowLimiter")


class SlidingLogLimiter:
    """TODO: exact — store per-key timestamps; admit iff fewer than N in (now-W, now]."""

    def __init__(self, limit: int, window_s: float) -> None:
        raise NotImplementedError("TODO: implement SlidingLogLimiter")


class SlidingWindowLimiter:
    """TODO: weighted interpolation between the previous and current windows."""

    def __init__(self, limit: int, window_s: float) -> None:
        raise NotImplementedError("TODO: implement SlidingWindowLimiter")


class TokenBucketLimiter:
    """TODO: capacity B, refill rate r; admit when a token is available."""

    def __init__(self, rate_per_s: float, capacity: float) -> None:
        raise NotImplementedError("TODO: implement TokenBucketLimiter")


class GcraLimiter:
    """TODO: virtual scheduling — theoretical arrival time (TAT) per key.

    The classic seeded bug: forgetting the ``max`` in the TAT update.
    """

    def __init__(self, rate_per_s: float, burst: int) -> None:
        raise NotImplementedError("TODO: implement GcraLimiter")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prove-limiters", description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("DRY RUN: run the 14 ported tests plus the non-integer-window test.")
        return 0
    print("Scaffold ready. Implement the five limiters in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
