"""Capstone 6.2 [mid] — Inventory API with a SQLite Repository.

Parts, stock levels, and reservations behind one repository protocol,
selected by pydantic-settings. See README.md for the contract.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Protocol, Sequence

from pydantic import BaseModel, Field

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"


class Part(BaseModel):
    sku: str = Field(pattern=r"^NWR-\d{4}$")
    name: str
    on_hand: int = Field(ge=0)


class Reservation(BaseModel):
    id: int
    sku: str
    quantity: int = Field(ge=1)
    status: str  # "reserved" | "shipped" | "cancelled"


class InventoryRepository(Protocol):
    """Both backends implement this seam; the suite runs against either."""

    def get_part(self, sku: str) -> Part | None: ...
    def reserve(self, sku: str, quantity: int) -> Reservation: ...
    def cancel(self, reservation_id: int) -> Reservation: ...
    def ping(self) -> bool: ...


class InMemoryInventoryRepository:
    """TODO: dict-backed implementation of InventoryRepository."""

    def __init__(self, parts: list[Part]) -> None:
        raise NotImplementedError("TODO: implement InMemoryInventoryRepository")


class SqliteInventoryRepository:
    """TODO: sqlite3-backed implementation; schema creation is idempotent.

    ``ping`` must actually exercise the database (return False when the
    file is unreadable), not just report that the object exists.
    """

    def __init__(self, db_path: Path) -> None:
        raise NotImplementedError("TODO: implement SqliteInventoryRepository")


class Settings(BaseModel):  # TODO: convert to pydantic_settings.BaseSettings
    """Selects the repository backend by name (``memory`` | ``sqlite``)."""

    backend: str = "memory"
    sqlite_path: Path = Path("inventory.db")


def load_parts_fixture() -> list[Part]:
    """Generate the 500 synthetic parts NWR-0001..NWR-0500 deterministically.

    TODO: 1% of rows deliberately invalid for negative tests (kept out of
    the valid return value but reproducible for the negative suite).
    """
    raise NotImplementedError("TODO: implement load_parts_fixture")


def create_app(settings: Settings | None = None) -> "object":
    """Build the FastAPI app wiring the settings-selected repository.

    TODO: reservation invariants map to 409 problem documents (cannot
    reserve more than on-hand; cannot cancel a shipped reservation);
    ``/ready`` returns 503 when the database is unreadable.
    """
    raise NotImplementedError("TODO: implement create_app")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="inventory-api", description=__doc__)
    parser.add_argument("--backend", choices=["memory", "sqlite"], default="memory")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print(f"DRY RUN: inventory API with backend={args.backend}")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
