"""Capstone 10.2 [junior] — Conditional-GET Sync Agent.

Poll the parts API on a fixed schedule and transfer bytes only when
representations actually changed. See README.md for the contract.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"


@dataclass
class ValidatorState:
    """Per-SKU validator state persisted to a local JSON file."""

    etag: str | None = None
    body: bytes = b""


@dataclass
class SyncStats:
    polls: int = 0
    bytes_transferred: int = 0
    zero_byte_syncs: int = 0


def load_state(path: Path) -> dict[str, ValidatorState]:
    """Load per-SKU validator state; an absent file means an empty mirror."""
    raise NotImplementedError("TODO: implement load_state")


def save_state(path: Path, state: dict[str, ValidatorState]) -> None:
    """Persist state deterministically (stable key ordering, atomic write)."""
    raise NotImplementedError("TODO: implement save_state")


def poll_sku(client: "object", sku: str, state: ValidatorState, stats: SyncStats) -> None:
    """One conditional GET.

    TODO: send If-None-Match when a validator exists; on 304 keep the stored
    body and count a zero-byte sync; on 200 replace state and add the body
    length to stats.bytes_transferred.
    """
    raise NotImplementedError("TODO: implement poll_sku")


def run_schedule(client: "object", skus: list[str], state_path: Path,
                 polls: int = 20) -> SyncStats:
    """Run the full poll schedule; return stats for the savings report.

    Contract: after every poll the local state equals the server's current
    representation; a mid-run restock is observed exactly once.
    """
    raise NotImplementedError("TODO: implement run_schedule")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sync-agent", description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--state", type=Path, default=Path("sync_state.json"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print(f"DRY RUN: 20 conditional-GET polls against {args.base_url}")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
