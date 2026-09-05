"""Smoke tests for the Capstone 6.1 scaffold — these pass out of the box.

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


@pytest.mark.skip(reason="TODO: implement create_app, then unskip")
def test_ten_route_tests_every_happy_path_404_two_422s():
    # TODO: >= 10 TestClient tests: every happy path, one 404, two distinct 422s.
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: implement models/repo, then unskip")
def test_ids_deterministic_per_fresh_app():
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: implement response models, then unskip")
def test_openapi_documents_422_for_every_body_route():
    raise NotImplementedError

