"""Smoke tests for the Capstone 16.3 scaffold — these pass out of the box.

Skipped tests are TODOs: implement the matching behavior in starter.py,
then unskip and flesh out the assertions. Everything is offline; tokens and
keys are synthetic lab material only.
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


@pytest.mark.skip(reason="TODO: implement fetchers, then unskip")
def test_naive_exploits_succeed_prefix_all_blocked_postfix():
    # TODO: one run demonstrates all three exploits succeed against the naive
    # fetcher and are blocked (SsrfBlocked) against the full SafeFetcher.
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: implement DNS pinning, then unskip")
def test_dns_rebinding_and_redirect_revalidation():
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: implement blame_table, then unskip")
def test_blame_table_covers_composition_only_layers():
    raise NotImplementedError

