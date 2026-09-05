"""Smoke tests for the capstone scaffold — these pass out of the box.

The skipped tests below are TODOs: implement the matching function in
starter.py, then remove the skip marker and flesh out the assertions.
"""

import importlib.util
import sys
from pathlib import Path

import pytest


def _load_starter():
    """Load this folder's starter.py by path.

    Loading by path (rather than ``import starter``) keeps the suite working
    from any working directory, even when sibling capstone folders ship
    same-named files.
    """
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
    """Smoke test: the scaffold loads and exposes an argparse CLI."""
    parser = starter.build_parser()
    assert parser.parse_args(["--seed", "7"]).seed == 7


def test_main_dry_run_exits_zero():
    """Smoke test: the CLI runs offline and exits 0 with --dry-run."""
    assert starter.main(["--dry-run"]) == 0


@pytest.mark.skip(reason="TODO: implement load_dataset in starter.py, then unskip")
def test_load_dataset_is_offline_and_deterministic():
    rows = starter.load_dataset("parts.csv")
    assert rows == starter.load_dataset("parts.csv")


@pytest.mark.skip(reason="TODO: implement run in starter.py, then unskip")
def test_run_completes_successfully():
    args = starter.build_parser().parse_args([])
    assert starter.run(args) == 0
