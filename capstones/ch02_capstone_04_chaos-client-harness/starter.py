"""Capstone 2.4 [senior] — Chaos-Client Harness.

A fault-injection transport between the resilient client and the stub that
proves, empirically, that the resilience policy works. See README.md.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Sequence

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"


class FaultKind(str, Enum):
    CONNECT_RESET = "connect_reset"
    READ_STALL = "read_stall"
    TRUNCATION = "truncation"
    BURST_500 = "burst_500"
    RATE_LIMIT_429 = "rate_limit_429"
    CONTENT_LENGTH_LIE = "content_length_lie"
    GZIP_BOMB = "gzip_bomb"
    SLOW_DRIP = "slow_drip"


@dataclass(frozen=True)
class Fault:
    """One scheduled fault. ``at_request`` is the 0-based request index."""

    kind: FaultKind
    at_request: int
    detail: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Expectation:
    """Executable contract: what the client must do under this fault."""

    fault: FaultKind
    outcome: str            # "recover" | "fail_fast" | "abort_bounded"
    max_attempts: int
    max_sleep_seconds: float
    max_buffered_bytes: int


class ChaosTransport:  # TODO: subclass httpx.BaseTransport
    """Wrap a MockTransport and inject the scheduled faults deterministically.

    TODO: implement ``handle_async_request``/``handle_request`` so each
    scheduled :class:`Fault` fires exactly at its request index; RNG is the
    injected seeded instance only.
    """

    def __init__(self, schedule: list[Fault], rng: random.Random) -> None:
        self.schedule = schedule
        self.rng = rng

    # TODO: def handle_request(self, request): ...


def load_schedule(path: Path) -> list[Fault]:
    """Parse a JSON fault schedule deterministically (stable ordering)."""
    raise NotImplementedError("TODO: implement load_schedule")


def run_gauntlet(schedule_path: Path, seed: int) -> dict[str, str]:
    """Run the SDK against every schedule; return fault -> observed behavior.

    TODO: assert per-fault :class:`Expectation` — outcome and bounds
    (attempts, sleep, buffered bytes) — and build the coverage report.
    """
    raise NotImplementedError("TODO: implement run_gauntlet")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chaos-client", description=__doc__)
    parser.add_argument("--schedule", type=Path, default=Path("fault_schedule.json"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print(f"DRY RUN: replay {args.schedule} with seed {args.seed}")
        return 0
    print("Scaffold ready. Implement the TODO functions in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
