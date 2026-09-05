"""Tests for mini_spectral.py, including a deliberately non-compliant spec."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import mini_spectral as ms

HERE = Path(__file__).parent
RULESET = HERE / "ruleset.yaml"
COMPLIANT = HERE / "specs" / "northwind_robots.yaml"
NONCOMPLIANT = HERE / "fixtures" / "noncompliant_spec.yaml"


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# End-to-end CLI behaviour (exit codes are the CI contract)
# --------------------------------------------------------------------------

def test_compliant_spec_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    code = ms.main([str(COMPLIANT), "--ruleset", str(RULESET)])
    out = capsys.readouterr().out
    assert code == 0
    assert "0 error(s)" in out


def test_noncompliant_spec_exits_one_and_names_rules(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = ms.main([str(NONCOMPLIANT), "--ruleset", str(RULESET)])
    out = capsys.readouterr().out
    assert code == 1
    for rule_id in (
        "info-contact-required",
        "semver-info-version",
        "path-segment-kebab-case",
        "operation-id-camel-case",
        "problem-json-errors",
        "pagination-required-on-lists",
    ):
        assert rule_id in out
    # violations carry JSON paths
    assert '$.paths["/RobotParts"].get.operationId' in out
    assert "6 error(s), 1 warning(s)" in out


def test_missing_file_exits_two(capsys: pytest.CaptureFixture[str]) -> None:
    code = ms.main([str(HERE / "nope.yaml"), "--ruleset", str(RULESET)])
    assert code == 2
    assert "cannot load input" in capsys.readouterr().err


def test_not_an_openapi_doc_exits_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bogus = tmp_path / "bogus.yaml"
    bogus.write_text("just: a mapping\n", encoding="utf-8")
    code = ms.main([str(bogus), "--ruleset", str(RULESET)])
    assert code == 2
    assert "OpenAPI" in capsys.readouterr().err


# --------------------------------------------------------------------------
# Unit behaviour of individual rule kinds
# --------------------------------------------------------------------------

def test_casing_patterns() -> None:
    assert ms.CASING_PATTERNS["kebab"].fullmatch("robot-parts")
    assert not ms.CASING_PATTERNS["kebab"].fullmatch("RobotParts")
    assert ms.CASING_PATTERNS["camel"].fullmatch("listRobots")
    assert not ms.CASING_PATTERNS["camel"].fullmatch("list_parts")


def test_resolve_pointer_missing() -> None:
    assert ms.resolve_pointer({"info": {}}, "/info/contact") is None
    assert ms.resolve_pointer({"info": {"contact": {}}}, "/info/contact") == {}


def test_template_path_params_are_not_linted_as_segments() -> None:
    doc = load(COMPLIANT)
    ruleset = {
        "rules": [
            {
                "id": "path-segment-kebab-case",
                "severity": "error",
                "kind": "casing",
                "target": "path_segment",
                "style": "kebab",
                "message": "kebab only",
            }
        ]
    }
    assert ms.lint(doc, ruleset) == []


def test_unknown_rule_kind_is_a_ruleset_error() -> None:
    doc = load(COMPLIANT)
    with pytest.raises(ValueError, match="unknown rule kind"):
        ms.lint(doc, {"rules": [{"id": "x", "severity": "error",
                                 "kind": "telepathy"}]})


def test_warn_severity_does_not_fail_build(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # The compliant spec trips the pagination rule if we demand a
    # non-existent parameter -- warnings must not change the exit code.
    ruleset_text = RULESET.read_text(encoding="utf-8").replace(
        "params: [limit, cursor]", "params: [limit, cursor, locale]"
    )
    violations = ms.lint(load(COMPLIANT), yaml.safe_load(ruleset_text))
    assert violations and all(v.severity == "warn" for v in violations)
