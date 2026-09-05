"""Capstone 16.5 [staff] — Full Red Team / Blue Team Exercise.

Two-sided exercise over a multi-service Northwind topology: exploits as
failing contract tests, fixes that keep the functional suite green.
Synthetic keys and data only. See README.md for the contract.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence


class FlawKind(str, Enum):
    BOLA = "bola"
    TOKEN_CONFUSION = "token-confusion"      # cross-service audience confusion
    MISSING_RATE_LIMIT = "missing-rate-limit"
    VERBOSE_ERROR = "verbose-error"
    WEAK_SECRET = "weak-secret"
    SSRF = "ssrf"
    MASS_ASSIGNMENT = "mass-assignment"
    MISSING_AUTH = "missing-auth"
    UNRESTRICTED_UPLOAD = "unrestricted-upload"
    STALE_JWKS = "stale-jwks"


@dataclass(frozen=True)
class SeededFlaw:
    kind: FlawKind
    service: str          # "fleet" | "billing"
    location: str
    owasp_item: str       # e.g. "API1:2023"


@dataclass
class Finding:
    flaw: SeededFlaw
    exploit_test: str = ""      # the failing contract test that documents it
    detection_signal: str = ""
    permanent_control: str = ""


def seed_environment() -> list[SeededFlaw]:
    """At least ten flaws across fleet and billing.

    Contract: includes exactly one cross-service token-confusion flaw
    (billing tokens accepted by fleet).
    """
    raise NotImplementedError("TODO: implement seed_environment")


def create_fleet_app(*, hardened: bool) -> "object":
    """The fleet service with the seeded flaws (or their fixes)."""
    raise NotImplementedError("TODO: implement create_fleet_app")


def create_billing_app(*, hardened: bool) -> "object":
    """The billing service with the seeded flaws (or their fixes)."""
    raise NotImplementedError("TODO: implement create_billing_app")


def exploit_audience_confusion(fleet_client: "object", billing_token: str) -> bool:
    """Red team: present a billing token to the fleet service.

    Contract: True against the seeded build; False once audience validation
    is fixed. This exploit is a contract test, not a slide.
    """
    raise NotImplementedError("TODO: implement exploit_audience_confusion")


def retro(findings: list[Finding]) -> str:
    """Render findings -> OWASP items -> detection -> permanent control."""
    raise NotImplementedError("TODO: implement retro")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="red-blue", description=__doc__)
    parser.add_argument("--hardened", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        mode = "hardened" if args.hardened else "seeded"
        print(f"DRY RUN: run red-team battery against the {mode} topology")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
