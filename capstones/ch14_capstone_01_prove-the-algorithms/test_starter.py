"""Smoke tests for the Capstone 14.1 scaffold — these pass out of the box.

Skipped tests are TODOs: implement the matching behavior in starter.py,
then unskip and flesh out the assertions. Everything is offline and seeded.
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


@pytest.mark.skip(reason="TODO: implement the five limiters, then unskip")
def test_ported_proof_sheet_passes_14_tests():
    # TODO: port the chapter's 14 tests unmodified against your reimplementation.
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: seed one bug per algorithm, then unskip")
def test_every_seeded_bug_is_caught_by_a_named_test():
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: implement FixedWindowLimiter, then unskip")
def test_fixed_window_2x_burst_with_non_integer_window():
    # TODO: W = 1.5; prove 20 admissions in a sub-window interval.
    raise NotImplementedError

