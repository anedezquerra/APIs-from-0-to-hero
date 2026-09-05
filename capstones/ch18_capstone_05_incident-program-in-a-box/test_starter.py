"""Smoke tests for the Capstone 18.5 scaffold — these pass out of the box.

Skipped tests are TODOs: implement the matching behavior in starter.py,
then unskip and flesh out the assertions. Everything is offline, in-process,
and seeded.
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


@pytest.mark.skip(reason="TODO: implement runbooks/SLOs, then unskip")
def test_slos_runbooks_dashboards_exist_and_cite_each_other():
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: implement game day, then unskip")
def test_game_day_timings_reproducible_from_seeds():
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: implement retry-storm script, then unskip")
def test_spans_per_trace_alert_fires_before_latency_burn_pages():
    raise NotImplementedError

