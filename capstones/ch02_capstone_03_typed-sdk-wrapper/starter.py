"""Capstone 2.3 [mid] — Typed SDK Wrapper with Full Test Matrix.

A local ``northwind-parts-sdk``: typed pydantic models, the resilient
client, pagination iterators, and a complete offline fault matrix.
See README.md for the contract.
"""

from __future__ import annotations

import argparse
from typing import Iterator, Sequence

from pydantic import BaseModel, Field

DATA_DIR_MSG = "Shared fixtures: ..\\..\\datasets\\northwind_robotics\\parts.csv"


class Part(BaseModel):
    """One catalog part. TODO: align fields with your Part JSON Schema."""

    sku: str = Field(pattern=r"^NWR-\d{4}$")
    name: str
    unit_price_cents: int = Field(ge=0)


class PartPage(BaseModel):
    """One page of a cursor-paginated catalog response."""

    items: list[Part]
    next_cursor: str | None = None


class ApiError(BaseModel):
    """Structured error body returned by the stub."""

    code: str
    message: str


class ApiContractError(Exception):
    """Response failed schema validation — never retried."""


class ApiTransientError(Exception):
    """Timeout / 5xx / 429 — retried within a bounded budget."""


class PartsClient:
    """Public SDK surface. Compose timeouts, pooling, auth, hooks, retries.

    TODO: wrap httpx.Client; every method returns typed models and raises
    only the typed errors above.
    """

    def get_part(self, sku: str) -> Part:
        """Fetch one part. Contract errors are never retried."""
        raise NotImplementedError("TODO: implement PartsClient.get_part")

    def iter_parts(self) -> Iterator[Part]:
        """Iterate the whole catalog through PartPage cursors."""
        raise NotImplementedError("TODO: implement PartsClient.iter_parts")

    def reserve(self, sku: str, quantity: int, *, idempotency_key: str) -> None:
        """Mutation calls must carry an idempotency key (enforced)."""
        raise NotImplementedError("TODO: implement PartsClient.reserve")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="parts-sdk-demo", description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print(f"DRY RUN: SDK demo against {args.base_url}")
        return 0
    print("Scaffold ready. Implement PartsClient in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
