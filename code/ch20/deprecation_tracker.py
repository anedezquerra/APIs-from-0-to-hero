r"""deprecation_tracker.py -- retirement readiness + communication schedule.

Reads a deprecation campaign registry (YAML) and produces:

  1. a retirement-readiness report (per consumer, plus traffic-weighted
     migration percentage), and
  2. the communication schedule relative to the kill date
     (announcement, reminders, brownouts, sunset, post-sunset audit).

The report is deterministic: the evaluation date is supplied explicitly
(--today) so CI output and this book's examples never drift.

Usage (PowerShell):
    python deprecation_tracker.py .\fixtures\deprecation_registry.yaml --today 2026-07-15
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml

# Statuses that block retirement even at zero reported traffic.
ACTIVE_STATUSES = ("in_progress", "not_started")

# Communication cadence, as offsets (in days) from the kill date.
# Brownouts (scheduled short 410 windows) are the escape hatch that flushes
# out consumers who ignore email -- see Chapters 9 and 14.
CADENCE: tuple[tuple[int, str, str], ...] = (
    (-180, "announcement", "all consumers: email + changelog + portal banner"),
    (-90, "reminder", "all consumers not yet migrated"),
    (-60, "reminder", "non-migrated consumers + their owning teams' leads"),
    (-30, "brownout #1", "1-hour 410 window, business hours, with notice"),
    (-14, "final warning", "non-migrated consumers, escalation to sponsors"),
    (-7, "brownout #2", "4-hour 410 window with notice"),
    (0, "sunset", "permanent HTTP 410 + final changelog entry"),
    (7, "post-sunset audit", "gateway log sweep for residual 410 traffic"),
)


@dataclass(frozen=True)
class Consumer:
    name: str
    owner: str
    tier: str
    status: str
    weekly_calls: int
    notes: str = ""


def load_registry(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "consumers" not in data:
        raise ValueError("registry must contain a 'consumers' list")
    return data


def parse_consumers(registry: dict[str, Any]) -> list[Consumer]:
    consumers = []
    for raw in registry["consumers"]:
        consumers.append(
            Consumer(
                name=str(raw["name"]),
                owner=str(raw.get("owner", "unknown")),
                tier=str(raw.get("tier", "internal")),
                status=str(raw.get("status", "not_started")),
                weekly_calls=int(raw.get("weekly_calls", 0)),
                notes=str(raw.get("notes", "")),
            )
        )
    return consumers


def readiness_report(
    registry: dict[str, Any], consumers: list[Consumer], today: date
) -> list[str]:
    kill = date.fromisoformat(str(registry["kill_date"]))
    # Migrated consumers no longer call v1, so the meaningful readiness
    # metric is residual traffic: calls still arriving from consumers that
    # have NOT finished migrating.
    residual = [c for c in consumers if c.status != "migrated"]
    residual_calls = sum(c.weekly_calls for c in residual)

    lines = [
        f"Retirement readiness: {registry['api']} {registry['version']} "
        f"(replacement: {registry.get('replacement', 'n/a')})",
        "=" * 72,
        f"today: {today.isoformat()}   kill date: {kill.isoformat()}   "
        f"days remaining: {(kill - today).days}",
        "",
        f"{'consumer':<22}{'tier':<10}{'status':<14}{'calls/wk':>10}  owner",
        "-" * 72,
    ]
    for c in sorted(consumers, key=lambda c: -c.weekly_calls):
        lines.append(
            f"{c.name:<22}{c.tier:<10}{c.status:<14}{c.weekly_calls:>10}  "
            f"{c.owner}"
        )
    lines += [
        "-" * 72,
        f"residual v1 traffic: {residual_calls} calls/wk across "
        f"{len(residual)} non-migrated consumer(s)",
        "",
    ]

    blockers = [
        c for c in consumers
        if c.status in ACTIVE_STATUSES
        or (c.status == "unresponsive" and c.weekly_calls > 0)
    ]
    if blockers:
        lines.append("verdict: NOT READY TO RETIRE -- blockers:")
        for c in blockers:
            lines.append(f"  - {c.name} ({c.status}, {c.weekly_calls} "
                         f"calls/wk): {c.notes}")
    else:
        lines.append("verdict: READY TO RETIRE -- no live traffic on "
                     "non-migrated consumers.")
    return lines


def schedule_report(registry: dict[str, Any]) -> list[str]:
    kill = date.fromisoformat(str(registry["kill_date"]))
    lines = [
        "",
        f"Communication schedule (kill date {kill.isoformat()})",
        "-" * 72,
        f"{'date':<12}{'T-minus':>9}  action / audience",
        "-" * 72,
    ]
    for offset, action, audience in CADENCE:
        when = kill + timedelta(days=offset)
        label = f"T{offset:+d}" if offset else "T-0"
        lines.append(f"{when.isoformat():<12}{label:>9}  {action}: {audience}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deprecation campaign tracker.")
    parser.add_argument("registry", type=Path, help="campaign registry YAML")
    parser.add_argument(
        "--today",
        required=True,
        help="evaluation date, ISO format (kept explicit for determinism)",
    )
    args = parser.parse_args(argv)

    try:
        today = date.fromisoformat(args.today)
    except ValueError:
        print("error: --today must be ISO format, e.g. 2026-07-15",
              file=sys.stderr)
        return 2
    try:
        registry = load_registry(args.registry)
        consumers = parse_consumers(registry)
    except (OSError, ValueError, KeyError, yaml.YAMLError) as exc:
        print(f"error: cannot parse registry: {exc}", file=sys.stderr)
        return 2

    for line in readiness_report(registry, consumers, today):
        print(line)
    for line in schedule_report(registry):
        print(line)
    # Non-zero exit while blocked so CI can gate the retirement runbook.
    blocked = any(
        c.status in ACTIVE_STATUSES
        or (c.status == "unresponsive" and c.weekly_calls > 0)
        for c in consumers
    )
    return 1 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
