"""Contract tests for the mini pact framework.

Run:  pytest test_pact_mini.py -q
"""
from __future__ import annotations

import json
from pathlib import Path

from pact_mini import PROVIDER_STATES, ProviderVerifier, record_demo_pact
from robot_registry import create_app


def test_recorded_pact_file_is_wellformed(tmp_path: Path) -> None:
    pact = record_demo_pact(tmp_path)
    document = json.loads(pact.read_text(encoding="utf-8"))
    assert document["consumer"]["name"] == "fulfillment-service"
    assert document["provider"]["name"] == "robot-registry"
    assert [i["description"] for i in document["interactions"]] == [
        "create a robot",
        "fetch robot 7",
    ]
    assert document["interactions"][1]["providerState"] == "a robot with id 7 exists"


def test_provider_satisfies_the_pact(tmp_path: Path) -> None:
    pact = record_demo_pact(tmp_path)
    report = ProviderVerifier(create_app, pact, PROVIDER_STATES).verify()
    print("\n" + report.render())
    assert report.ok, report.failures()


def test_breaking_field_rename_is_caught(tmp_path: Path) -> None:
    """The provider renames ``sku`` -> ``part_number``: verification must fail."""
    pact = record_demo_pact(tmp_path)
    report = ProviderVerifier(
        lambda: create_app(breaking=True), pact, PROVIDER_STATES
    ).verify()
    print("\n" + report.render())
    assert not report.ok
    rendered = report.render()
    assert "sku" in rendered  # the missing field is named in the report


def test_unknown_provider_state_fails_loudly(tmp_path: Path) -> None:
    pact = record_demo_pact(tmp_path)
    document = json.loads(pact.read_text(encoding="utf-8"))
    document["interactions"][1]["providerState"] = "a robot with id 99 exists"
    pact.write_text(json.dumps(document), encoding="utf-8")
    report = ProviderVerifier(create_app, pact, PROVIDER_STATES).verify()
    assert not report.ok
    assert any("unknown provider state" in f for f in report.failures())
