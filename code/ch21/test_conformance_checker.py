"""Tests for the architecture conformance checker.

Runs against two synthetic fixture folders: ``fixtures_pass`` (a
compliant Northwind manifests folder) and ``fixtures_fail`` (a legacy
folder that breaches every rule family).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conformance_checker import check_folder, main

HERE = Path(__file__).parent
PASS_DIR = HERE / "fixtures_pass"
FAIL_DIR = HERE / "fixtures_fail"


def test_compliant_folder_passes() -> None:
    assert check_folder(PASS_DIR) == []


def test_legacy_folder_fails() -> None:
    violations = check_folder(FAIL_DIR)
    assert violations, "legacy folder must produce violations"


def test_every_rule_family_fires_on_legacy_folder() -> None:
    rules = {v.rule for v in check_folder(FAIL_DIR)}
    assert {"O-001", "O-002", "O-003", "O-004", "A-001"} <= rules


def test_main_exit_codes() -> None:
    assert main(["prog", str(PASS_DIR)]) == 0
    assert main(["prog", str(FAIL_DIR)]) == 1


def test_missing_folder_exit_code() -> None:
    assert main(["prog", str(HERE / "no_such_dir")]) == 2


def test_checker_is_deterministic() -> None:
    assert check_folder(FAIL_DIR) == check_folder(FAIL_DIR)


def test_asyncapi_ref_payload_is_resolved(tmp_path: Path) -> None:
    """A publish payload referenced via components must not false-positive."""
    spec = tmp_path / "ref.asyncapi.yaml"
    spec.write_text(
        "\n".join(
            [
                'asyncapi: "2.6.0"',
                "info: { title: Ref Events, version: '1.0.0' }",
                "channels:",
                "  robot.readings:",
                "    publish:",
                "      message: { $ref: '#/components/messages/Reading' }",
                "components:",
                "  messages:",
                "    Reading:",
                "      payload: { $ref: '#/components/schemas/Envelope' }",
                "  schemas:",
                "    Envelope:",
                "      type: object",
                "      properties:",
                "        event_id: { type: string }",
                "        occurred_at: { type: string, format: date-time }",
            ]
        ),
        encoding="utf-8",
    )
    assert check_folder(tmp_path) == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
