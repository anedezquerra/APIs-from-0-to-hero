"""Smoke tests for the docs, funnel, deprecation, and catalog tools."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml

import catalog_manifest
import deprecation_tracker
import docs_generator
import ttfc_funnel

HERE = Path(__file__).parent


def test_docs_generator_renders_endpoints_and_schemas() -> None:
    spec = yaml.safe_load(
        (HERE / "specs" / "northwind_robots.yaml").read_text(encoding="utf-8")
    )
    md = docs_generator.render_markdown(spec)
    assert "# Northwind Robotics Fleet API" in md
    assert "### `GET /robots`" in md
    assert "application/problem+json -> Problem" in md
    assert "[classification: internal]" in md  # data classification surfaced


def test_funnel_counts_and_ttfc() -> None:
    journeys, skipped = ttfc_funnel.load_journeys(
        HERE / "fixtures" / "onboarding_events.jsonl"
    )
    assert skipped == 0
    assert len(journeys) == 60
    assert len(ttfc_funnel.reached(journeys, "first_200")) == 24
    ttfc = ttfc_funnel.median_gap_minutes(journeys, "signup", "first_200")
    assert ttfc == pytest.approx(431.0)


def test_funnel_survives_malformed_lines(tmp_path: Path) -> None:
    bad = tmp_path / "events.jsonl"
    bad.write_text(
        '{"ts": "2026-03-02T09:00:00Z", "developer_id": "d1", '
        '"event": "signup"}\nnot json at all\n',
        encoding="utf-8",
    )
    journeys, skipped = ttfc_funnel.load_journeys(bad)
    assert skipped == 1 and len(journeys) == 1


def test_deprecation_tracker_blocked_and_schedule() -> None:
    registry = deprecation_tracker.load_registry(
        HERE / "fixtures" / "deprecation_registry.yaml"
    )
    consumers = deprecation_tracker.parse_consumers(registry)
    report = "\n".join(
        deprecation_tracker.readiness_report(
            registry, consumers, today=date(2026, 7, 15)
        )
    )
    assert "NOT READY TO RETIRE" in report
    assert "legacy-billing-hook" in report  # the shadow API shows up
    schedule = "\n".join(deprecation_tracker.schedule_report(registry))
    assert "T-0" in schedule and "brownout #2" in schedule


def test_catalog_manifest_scans_both_specs() -> None:
    manifests, warnings = catalog_manifest.scan(HERE / "specs")
    assert warnings == []
    names = {m["metadata"]["name"] for m in manifests}
    assert names == {
        "northwind-robotics-fleet-api",
        "northwind-robotics-telemetry-api",
    }
    assert all(m["kind"] == "API" for m in manifests)
    assert manifests[0]["spec"]["owner"].startswith("team-")
