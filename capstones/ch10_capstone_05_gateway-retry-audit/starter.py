"""Capstone 10.5 [staff] — Correctness Audit of a Retry-Capable Gateway.

Enumerate retry sources, classify mutation endpoints by idempotency posture,
and produce the remediation and telemetry plan. See README.md.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Sequence

DATA_DIR = Path(__file__).resolve().parents[2] / "datasets" / "northwind_robotics"
REGISTRY_PATH = Path(__file__).resolve().parent / "platform_registry.yaml"


class Posture(str, Enum):
    SPEC_IDEMPOTENT = "spec-idempotent"   # e.g. PUT/DELETE by design
    KEY_PROTECTED = "key-protected"       # idempotency-key protocol in place
    UNPROTECTED = "unprotected"           # unsafe and reachable by a retry source


@dataclass(frozen=True)
class Endpoint:
    path: str
    method: str
    retry_sources: tuple[str, ...]        # client_sdk | proxy | lb | queue
    posture: Posture


@dataclass(frozen=True)
class Finding:
    """One lint finding: an unprotected unsafe endpoint a retry source can duplicate."""

    endpoint: str
    method: str
    retry_sources: tuple[str, ...]
    remediation: str = ""


def load_registry(path: Path = REGISTRY_PATH) -> list[Endpoint]:
    """Parse the platform registry.

    TODO: YAML via pyyaml (or a JSON twin to stay stdlib-only); validate
    method vocabulary and retry-source vocabulary at load.
    """
    raise NotImplementedError("TODO: implement load_registry")


def lint(endpoints: list[Endpoint]) -> list[Finding]:
    """Flag unprotected unsafe methods reachable by any retry source.

    Contract: flags exactly the seeded violations — zero false positives on
    protected endpoints; output ordering deterministic (sorted by path).
    """
    raise NotImplementedError("TODO: implement lint")


def remediate(findings: list[Finding]) -> list[Finding]:
    """Attach a remediation to each finding.

    Contract: every remediation names the enforcing mechanism (unique
    constraint, fingerprint, fencing token) — never just a header.
    """
    raise NotImplementedError("TODO: implement remediate")


def telemetry_plan() -> dict[str, str]:
    """Ongoing signals: replay rate, 409 rate, 422 rate, alert thresholds.

    Contract: at least one alert per failure mode of the chapter's war
    story; includes the blast radius of the key store being unavailable.
    """
    raise NotImplementedError("TODO: implement telemetry_plan")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="retry-audit", description=__doc__)
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print(f"DRY RUN: audit registry {args.registry}")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
