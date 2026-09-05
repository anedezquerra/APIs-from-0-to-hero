"""Capstone 16.2 [mid] — Scope Forge & Token Gauntlet.

A toy resource server with the full token-validation pipeline and a scope
model, attacked by a forgery battery. Synthetic keys only. See README.md.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class Scope(str, Enum):
    """Fleet-domain scope vocabulary. TODO: justify each granularity in the
    scope design document (coarse vs. fine trade-off)."""

    FLEET_READ = "fleet:read"
    FLEET_WRITE = "fleet:write"
    TELEMETRY_INGEST = "telemetry:ingest"


@dataclass(frozen=True)
class ValidatedToken:
    subject: str
    scopes: frozenset[str]
    audience: str
    issuer: str


class TokenRejected(Exception):
    """401 — carries the WWW-Authenticate diagnostics value."""

    def __init__(self, www_authenticate: str) -> None:
        super().__init__(www_authenticate)
        self.www_authenticate = www_authenticate


class ScopeInsufficient(Exception):
    """403 — token valid, required scope missing."""


def validate_token(token: str, *, jwks: dict, audience: str, issuer: str) -> ValidatedToken:
    """Full validation pipeline.

    TODO: verify the signature BEFORE reading any claim (an unsigned token
    carrying admin claims must be rejected, never honored); check exp, aud,
    iss, kid; every rejection carries WWW-Authenticate diagnostics.
    """
    raise NotImplementedError("TODO: implement validate_token")


def require_scope(token: ValidatedToken, required: Scope) -> None:
    """Raise ScopeInsufficient unless ``required`` is present."""
    raise NotImplementedError("TODO: implement require_scope")


def create_app(*, jwks: dict) -> "object":
    """Three endpoints, three different required scopes. TODO: build it."""
    raise NotImplementedError("TODO: implement create_app")


def forgery_battery(jwks: dict) -> dict[str, str]:
    """The seven forgeries: expired, wrong aud, wrong iss, alg=none, unknown
    kid, tampered payload, missing scope.

    TODO: return {forgery_name: token_string}; every one must produce
    401/403 against the app, never 200.
    """
    raise NotImplementedError("TODO: implement forgery_battery")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scope-forge", description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("DRY RUN: validate the 7-forgery battery against the resource server")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
