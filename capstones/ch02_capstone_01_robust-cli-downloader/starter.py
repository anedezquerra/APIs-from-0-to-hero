"""Capstone 2.1 [junior] — Robust CLI Downloader (``nrget``).

Download a part's datasheet from the local Northwind stub to a local file,
correctly and observably. See README.md for the full contract.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"

EXIT_OK = 0
EXIT_CLIENT_ERROR = 2
EXIT_SERVER_ERROR = 3


class DownloadError(Exception):
    """Base of the typed download error taxonomy."""


class ClientError(DownloadError):
    """4xx response: the caller must fix the request; never retried."""


class ServerError(DownloadError):
    """5xx or transport failure after bounded retries; safe to retry later."""


@dataclass(frozen=True)
class DownloadPlan:
    """What will be fetched and where it lands."""

    url: str
    output: Path
    max_bytes: int | None


@dataclass(frozen=True)
class DownloadResult:
    """What actually happened."""

    path: Path
    bytes_written: int
    status_code: int


def build_client() -> "object":
    """Return an ``httpx.Client`` with explicit four-dimension timeouts.

    TODO: construct the client with connect/read/write/pool timeouts set
    (no default/None timeout anywhere) and connection pooling limits.
    """
    raise NotImplementedError("TODO: build an httpx.Client with explicit timeouts")


def plan_download(args: argparse.Namespace) -> DownloadPlan:
    """Turn parsed CLI args into a validated :class:`DownloadPlan`.

    TODO: resolve the export URL, the output path, and ``--max-bytes``.
    Contract: never performs I/O; rejects empty output paths.
    """
    raise NotImplementedError("TODO: implement plan_download")


def download(plan: DownloadPlan) -> DownloadResult:
    """Stream the body to ``<output>.part`` and atomically rename on success.

    TODO: stream with ``iter_bytes``, enforce ``max_bytes`` mid-stream,
    retry transient failures within a bounded budget, and guarantee that a
    failed or interrupted run leaves no partial artifact. Progress goes to
    the console as byte counts; log method/path/status/latency only.
    """
    raise NotImplementedError("TODO: implement download")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nrget", description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000/catalog/export")
    parser.add_argument("--output", type=Path, default=Path("catalog_export.ndjson"))
    parser.add_argument("--max-bytes", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the request plan without sending anything.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print(f"DRY RUN: GET {args.url} -> {args.output} (max_bytes={args.max_bytes})")
        return EXIT_OK
    try:
        result = download(plan_download(args))
    except NotImplementedError:
        print("Scaffold ready. Implement the TODO functions in starter.py to begin.")
        return EXIT_OK
    except ClientError as exc:
        print(f"client error: {exc}")
        return EXIT_CLIENT_ERROR
    except ServerError as exc:
        print(f"server error: {exc}")
        return EXIT_SERVER_ERROR
    print(f"wrote {result.bytes_written} bytes to {result.path}")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
