"""Capstone 21.1 [junior] — Extend the Decision Advisor.

Questionnaire mode, a seventh data-residency criterion, and --explain over
the chapter's protocol advisor. See README.md for the contract.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Sequence

PROFILES = ("rest", "graphql", "grpc", "webhooks", "sse")

CRITERIA = (
    "payload_shape",
    "client_diversity",
    "latency_budget",
    "streaming",
    "tooling_maturity",
    "team_experience",
    "data_residency",   # the added seventh criterion
)


@dataclass(frozen=True)
class Answers:
    """One questionnaire run: criterion -> signal value."""

    values: dict[str, str]


@dataclass
class ScoreTable:
    """Full score table: profile -> score, with rationale traces."""

    scores: dict[str, float] = field(default_factory=dict)
    rationale: dict[str, list[str]] = field(default_factory=dict)

    def winner(self) -> str:
        raise NotImplementedError("TODO: implement ScoreTable.winner")

    def render_explain(self) -> str:
        """The --explain table for all five profiles, not only the winner."""
        raise NotImplementedError("TODO: implement ScoreTable.render_explain")


def score(answers: Answers) -> ScoreTable:
    """Score all profiles.

    Contract: the residency criterion penalizes public-CDN-dependent
    profiles when residency forbids edge caching; rationale traces mention
    residency when it moved a score; no existing winner flips on the
    canonical scenarios.
    """
    raise NotImplementedError("TODO: implement score")


def questionnaire() -> Answers:
    """Interactive mode: prompt for the criteria, reject invalid answers
    with a clear message. Must run fully offline."""
    raise NotImplementedError("TODO: implement questionnaire")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="protocol-advisor", description=__doc__)
    parser.add_argument("--explain", action="store_true")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print(f"DRY RUN: score {len(PROFILES)} profiles over {len(CRITERIA)} criteria")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
