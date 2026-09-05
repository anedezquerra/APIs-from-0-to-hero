"""Smoke tests for the Capstone 2.2 scaffold — these pass out of the box.

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


@pytest.mark.skip(reason="TODO: implement TokenBucket, then unskip")
def test_bucket_never_exceeds_rate_with_injected_clock():
    # TODO: drive acquire() with a fake clock/sleep; assert sustained rate <= r.
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: implement retry policy, then unskip")
def test_retry_after_overrides_jitter_exactly():
    # TODO: forced-429 MockTransport with Retry-After: 3 must sleep exactly 3s
    # on the injected clock, ignoring jitter.
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: implement crawl, then unskip")
def test_full_crawl_has_zero_steady_state_429s(tmp_path):
    # TODO: crawl the 500-part MockTransport catalog; assert report.pages > 0,
    # report.retries_429 <= 1 (documented cold-start), and the evidence CSV
    # supports achieved_rate() <= 5.
    raise NotImplementedError

