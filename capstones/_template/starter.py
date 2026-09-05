"""TODO: <Capstone title> — starter scaffold.

Chapter <NN>, Capstone <MM> ([<difficulty>]) of
"Mastering APIs: From Zero to Production Guru".

Conventions: Python 3.11+, fully typed, offline-first, deterministic
(seed all randomness), synthetic Northwind Robotics data only.
The TODO markers below are intentional — they are the work items.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

# Shared synthetic datasets live at <repo>\datasets\northwind_robotics\.
# From this folder that is: ..\..\datasets\northwind_robotics\
DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"


def load_dataset(name: str) -> list[dict[str, str]]:
    """Load one synthetic dataset by file name (e.g. ``"parts.csv"``).

    TODO: read ``DATA_DIR / name`` deterministically and return parsed rows.

    Contract: never touches the network; raises :class:`FileNotFoundError`
    with an actionable message when the dataset is absent; identical bytes
    in produce identical rows out (no dict-ordering or time dependence).
    """
    raise NotImplementedError("TODO: implement load_dataset")


def run(args: argparse.Namespace) -> int:
    """Execute the capstone's main workflow.

    TODO: implement per the README's Steps section. Keep console output
    deterministic; print a short result summary, not debug noise.

    Returns a process exit code: 0 on success.
    """
    raise NotImplementedError("TODO: implement run")


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser. Add project-specific flags as the README requires."""
    parser = argparse.ArgumentParser(
        prog="capstone",
        description="Capstone scaffold — see README.md for objective and steps.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DATA_DIR,
        help="Path to the synthetic northwind_robotics datasets folder.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed for any randomized behavior (results must be reproducible).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan of work without executing it.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("Dry run: implement the TODO functions in starter.py to begin.")
        return 0
    try:
        return run(args)
    except NotImplementedError:
        print("Scaffold ready. Implement the TODO functions in starter.py to begin.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
