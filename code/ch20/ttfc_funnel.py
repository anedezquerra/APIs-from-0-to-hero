r"""ttfc_funnel.py -- onboarding funnel and time-to-first-call analytics.

Reads a JSONL event log (one synthetic onboarding event per line) and
computes the activation funnel

    signup -> key_issued -> first_call -> first_200

with per-step absolute counts, step-to-step conversion, and median
elapsed minutes between steps. TTFC is reported as the median time from
signup to first_200 -- the first moment a developer received a *useful*
response.

Usage (PowerShell):
    python ttfc_funnel.py .\fixtures\onboarding_events.jsonl
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

FUNNEL_STEPS = ("signup", "key_issued", "first_call", "first_200")


@dataclass
class DeveloperJourney:
    """First occurrence of each funnel step for one developer."""

    first_seen: dict[str, datetime] = field(default_factory=dict)


def parse_ts(raw: str) -> datetime:
    return datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ")


def load_journeys(path: Path) -> tuple[dict[str, DeveloperJourney], int]:
    """Build per-developer journeys; returns (journeys, skipped_lines)."""
    journeys: dict[str, DeveloperJourney] = {}
    skipped = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                dev = str(record["developer_id"])
                event = str(record["event"])
                ts = parse_ts(str(record["ts"]))
            except (ValueError, KeyError, TypeError):
                skipped += 1  # never let one bad line kill the report
                continue
            if event not in FUNNEL_STEPS:
                continue  # telemetry like docs_viewed is not a funnel step
            journey = journeys.setdefault(dev, DeveloperJourney())
            journey.first_seen.setdefault(event, ts)
    return journeys, skipped


def reached(journeys: dict[str, DeveloperJourney], step: str) -> set[str]:
    """Developers who completed this step AND every step before it."""
    index = FUNNEL_STEPS.index(step)
    required = FUNNEL_STEPS[: index + 1]
    return {
        dev
        for dev, journey in journeys.items()
        if all(s in journey.first_seen for s in required)
    }


def median_gap_minutes(
    journeys: dict[str, DeveloperJourney], start: str, end: str
) -> float | None:
    gaps = [
        (j.first_seen[end] - j.first_seen[start]).total_seconds() / 60.0
        for j in journeys.values()
        if start in j.first_seen and end in j.first_seen
    ]
    return statistics.median(gaps) if gaps else None


def build_report(journeys: dict[str, DeveloperJourney]) -> list[str]:
    lines = [
        "Onboarding funnel (unique developers, ordered steps)",
        "=" * 68,
        f"{'step':<14}{'reached':>9}{'step conv.':>12}{'cum. conv.':>12}"
        f"{'median gap (min)':>18}",
        "-" * 68,
    ]
    total = len(reached(journeys, FUNNEL_STEPS[0])) or 1  # avoid div-by-zero
    previous_count: int | None = None
    previous_step: str | None = None
    for step_name in FUNNEL_STEPS:
        count = len(reached(journeys, step_name))
        step_conv = (
            100.0 * count / previous_count
            if previous_count
            else 100.0
        )
        gap = (
            median_gap_minutes(journeys, previous_step, step_name)
            if previous_step
            else None
        )
        lines.append(
            f"{step_name:<14}{count:>9}{step_conv:>11.1f}%"
            f"{100.0 * count / total:>11.1f}%"
            f"{('n/a' if gap is None else f'{gap:.0f}'):>18}"
        )
        previous_count, previous_step = count, step_name

    ttfc = median_gap_minutes(journeys, "signup", "first_200")
    lines += [
        "-" * 68,
        f"TTFC (median signup -> first_200): "
        f"{('n/a' if ttfc is None else f'{ttfc:.0f} minutes')} "
        f"({('' if ttfc is None else f'{ttfc / 60:.1f} h')})",
    ]
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TTFC funnel analytics.")
    parser.add_argument("events", type=Path, help="JSONL onboarding events")
    args = parser.parse_args(argv)

    try:
        journeys, skipped = load_journeys(args.events)
    except OSError as exc:
        print(f"error: cannot read events: {exc}", file=sys.stderr)
        return 2
    if not journeys:
        print("error: no usable events found", file=sys.stderr)
        return 2

    for line in build_report(journeys):
        print(line)
    if skipped:
        print(f"note: skipped {skipped} malformed line(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
