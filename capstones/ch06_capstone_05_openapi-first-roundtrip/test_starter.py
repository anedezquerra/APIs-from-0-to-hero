"""Smoke tests for the Capstone 6.5 scaffold — these pass out of the box.

Skipped tests are TODOs: implement the matching behavior in starter.py,
then unskip and flesh out the assertions. Everything runs offline with
FastAPI's TestClient and seeded fixtures.
"""

import importlib.util
import sys
from pathlib import Path

import pytest


def _load_starter():
    """Load this folder's starter.py by path (safe across same-named siblings)."""
    path = Path(__file__).resolve().parent / "starter.py"
    name = "capstone_starter_" + path.parent.name.replace("-", "_")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolve cls.__module__ via sys.modules at class-creation time.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


starter = _load_starter()


def test_scaffold_exposes_cli():
    parser = starter.build_parser()
    assert parser.parse_args([]) is not None


def test_main_dry_run_exits_zero():
    assert starter.main(["--dry-run"]) == 0


@pytest.mark.skip(reason="TODO: implement diff_specs, then unskip")
def test_gate_classifies_seeded_compatible_and_breaking_changes():
    # TODO: optional `priority` field -> COMPATIBLE; field rename -> BREAKING,
    # both with human-readable reasons.
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: implement create_app + gate, then unskip")
def test_running_service_passes_its_own_gate_zero_diffs():
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: implement typed client, then unskip")
def test_typed_client_consumes_service_no_hand_edited_models():
    raise NotImplementedError

