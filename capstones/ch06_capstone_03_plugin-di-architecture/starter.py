"""Capstone 6.3 [senior] — Plugin-Style Dependency-Injection Architecture.

Repositories, notifiers, and pricing policies as registry plugins selected
by settings and composed in the lifespan. See README.md for the contract.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable, Protocol, Sequence

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"


class Notifier(Protocol):
    """Plugin protocol: called on order status changes."""

    def notify(self, order_id: int, status: str) -> None: ...


class PricingPolicy(Protocol):
    """Plugin protocol: prices an order at creation time."""

    def price_cents(self, lines: list[dict]) -> int: ...


Registry = dict[str, Callable[[], object]]

NOTIFIERS: Registry = {}
PRICING_POLICIES: Registry = {}


def register(registry: Registry, name: str) -> Callable:
    """Decorator adding a factory to a plugin registry.

    TODO: reject duplicate names with an actionable error.
    """
    raise NotImplementedError("TODO: implement register")


def resolve(registry: Registry, name: str) -> object:
    """Instantiate the plugin selected by settings.

    Contract: unknown names fail fast — at startup, with an error message
    naming the unknown plugin and listing the registered choices.
    """
    raise NotImplementedError("TODO: implement resolve")


class Settings:  # TODO: pydantic_settings.BaseSettings with env prefix NWR_
    notifier: str = "webhook-log"
    pricing: str = "list"


# --- Built-in plugins (studies for your own) --------------------------------

def make_webhook_log_notifier() -> Notifier:
    """TODO: notifier appending delivery records to a webhook log."""
    raise NotImplementedError("TODO: implement webhook-log notifier")


def make_audit_ndjson_notifier() -> Notifier:
    """TODO: notifier appending one NDJSON audit line per status change."""
    raise NotImplementedError("TODO: implement audit-ndjson notifier")


def make_list_pricing() -> PricingPolicy:
    """TODO: list-price policy."""
    raise NotImplementedError("TODO: implement list pricing")


def make_fleet_discount_pricing() -> PricingPolicy:
    """TODO: fleet-discount policy."""
    raise NotImplementedError("TODO: implement fleet-discount pricing")


def create_app(settings: Settings | None = None) -> "object":
    """Compose the selected plugin set in the lifespan and thread it through DI.

    TODO: price on order create; notify on status change; every dependency
    swappable per test via ``app.dependency_overrides`` without route edits.
    """
    raise NotImplementedError("TODO: implement create_app")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="orders-plugins", description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("DRY RUN: would boot the plugin-composed Orders API.")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
