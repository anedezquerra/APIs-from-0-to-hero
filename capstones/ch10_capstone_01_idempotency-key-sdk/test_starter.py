"""Smoke tests for the Capstone 10.1 scaffold — these pass out of the box.

Skipped tests are TODOs: implement the matching behavior in starter.py,
then unskip and flesh out the assertions. Everything runs offline and
deterministically (seeded, no wall-clock assertions).
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


@pytest.mark.skip(reason="TODO: implement submit, then unskip")
def test_retried_submit_yields_exactly_one_ledger_entry():
    # TODO: MockTransport that fails twice then succeeds; assert one mutation.
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: implement submit, then unskip")
def test_422_never_retried_409_retried_with_backoff():
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: implement Operation, then unskip")
def test_second_operation_mints_fresh_key():
    raise NotImplementedError

