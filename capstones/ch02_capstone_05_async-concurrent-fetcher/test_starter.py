"""Smoke tests for the Capstone 2.5 scaffold — these pass out of the box.

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


@pytest.mark.skip(reason="TODO: implement ConcurrentFetcher, then unskip")
def test_full_queue_drains_with_zero_pool_timeouts():
    # TODO: asyncio.run over a MockTransport stub; assert zero unhandled
    # exceptions and zero pool timeouts at the chosen settings.
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: implement AsyncTokenBucket, then unskip")
def test_sustained_rate_below_limit_429_rate_near_zero():
    # TODO: evidence from stub-side request log, not wall-clock assertions.
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: implement cancellation, then unskip")
def test_cancellation_leaves_no_orphan_tasks_or_partial_artifacts():
    raise NotImplementedError

