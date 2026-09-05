"""Capstone 14.2 [mid] — Header-Complete Middleware.

Platform-grade rate-limit middleware: Redis-backed limiter behind a
protocol, IETF RateLimit headers, RFC 9457 429 bodies, fail-open degraded
signal. See README.md for the contract.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class Decision:
    allowed: bool
    remaining: int
    reset_after_s: float
    retry_after_s: float | None


class KeyedLimiter(Protocol):
    """The seam: in-process for tests, Redis-backed for production shape."""

    def check(self, key: str) -> Decision: ...


class RedisLimiter:
    """TODO: sliding-window limiter over a Redis-like client (fakeredis offline).

    Contract: implements ``reset_after`` correctly; behaves identically to
    the chapter's in-process limiter so its tests pass unmodified.
    """

    def __init__(self, client: "object", limit: int, window_s: int) -> None:
        raise NotImplementedError("TODO: implement RedisLimiter")


@dataclass(frozen=True)
class Policy:
    """A published policy, e.g. ``"100;w=60"``."""

    limit: int
    window_s: int

    def as_header(self) -> str:
        """Render as a RateLimit-Policy value, e.g. ``100;w=60``."""
        raise NotImplementedError("TODO: implement Policy.as_header")


def problem_429(policy: Policy, retry_after_s: float) -> dict:
    """RFC 9457-style problem body for a rejected request.

    Contract: includes the policy and a documentation link; validates
    against the declared problem-details schema in the test suite.
    """
    raise NotImplementedError("TODO: implement problem_429")


def rate_limit_middleware(app: "object", limiter: KeyedLimiter, policy: Policy,
                          *, fail_open: bool) -> "object":
    """Wrap the app with header-complete limiting.

    TODO: on allow emit RateLimit-* fields; on deny emit 429 + problem body
    + Retry-After; on limiter failure either fail open (omit RateLimit-*,
    emit X-NR-Limiter-Degraded: true) or fail closed (503 + Retry-After).
    401 (unauthenticated) and 429 (throttled) must stay separated.
    """
    raise NotImplementedError("TODO: implement rate_limit_middleware")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rate-limit-middleware", description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("DRY RUN: mount middleware over /telemetry, /fleet/status, /reports/export, /health")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
