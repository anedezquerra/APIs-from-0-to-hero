"""Capstone 2.2 [mid] — Rate-Limit-Aware Catalog Crawler.

Crawl a 500-part cursor-paginated catalog under a published 5 req/s limit
without being throttled in steady state. See README.md for the contract.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Sequence

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"


@dataclass
class TokenBucket:
    """Client-side token bucket pacing every request.

    TODO: implement ``acquire`` so that sustained rate never exceeds
    ``rate`` tokens/second with burst capacity ``capacity``. The clock and
    sleep functions are constructor-injected so tests are deterministic.
    """

    rate: float = 4.0
    capacity: float = 4.0

    def acquire(self) -> None:
        """Block (via the injected sleep) until one token is available."""
        raise NotImplementedError("TODO: implement TokenBucket.acquire")


@dataclass(frozen=True)
class RequestRecord:
    """One request observation, appended to the evidence CSV."""

    page: int
    timestamp: float
    status: int


@dataclass
class CrawlReport:
    pages: int = 0
    parts: int = 0
    retries_429: int = 0
    records: list[RequestRecord] = field(default_factory=list)

    def achieved_rate(self) -> float:
        """Sustained requests/second computed from recorded timestamps."""
        raise NotImplementedError("TODO: compute rate from self.records")


def iter_pages(client: "object") -> Iterator[dict]:
    """Yield decoded pages by following the stub's cursor until exhaustion."""
    raise NotImplementedError("TODO: implement the cursor iterator")


def retry_after_seconds(response: "object") -> float | None:
    """Return the Retry-After hint in seconds, or None when absent.

    Contract: when present, this value overrides computed backoff jitter.
    """
    raise NotImplementedError("TODO: parse Retry-After")


def crawl(client: "object", bucket: TokenBucket, evidence_csv: Path) -> CrawlReport:
    """Drain the catalog: bucket-gate every request, retry per policy, log evidence.

    TODO: steady-state must see zero 429s; every request appends a
    :class:`RequestRecord` row to ``evidence_csv``.
    """
    raise NotImplementedError("TODO: implement crawl")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="catalog-crawler", description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--evidence", type=Path, default=Path("crawl_evidence.csv"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print(f"DRY RUN: crawl {args.base_url}/parts, evidence -> {args.evidence}")
        return 0
    print("Scaffold ready. Implement the TODO functions in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
