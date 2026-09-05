"""Smoke tests for the Capstone 2.4 scaffold — these pass out of the box.

Skipped tests are TODOs: implement the matching behavior in starter.py,
then unskip and flesh out the assertions. Everything runs offline against
httpx.MockTransport and seeded fixtures.
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


@pytest.mark.skip(reason="TODO: implement ChaosTransport, then unskip")
def test_eight_fault_classes_each_have_executable_expectation():
    # TODO: every FaultKind maps to an Expectation; >= 8 classes exercised.
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: implement run_gauntlet, then unskip")
def test_run_reproducible_from_seed_no_wall_clock():
    # TODO: two runs with seed=42 produce byte-identical coverage reports.
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: implement budget-exceeding fault, then unskip")
def test_fault_beyond_retry_budget_fails_fast_with_typed_error():
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: implement gzip bomb guard, then unskip")
def test_decompression_bomb_engages_size_guard():
    raise NotImplementedError

