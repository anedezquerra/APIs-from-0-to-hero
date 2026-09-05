"""Grand Capstone smoke tests — pass out of the box.

Skipped tests are the milestone acceptance TODOs: implement the services and
specs, then unskip the matching milestone test.
"""

from pathlib import Path

import pytest

PLATFORM_ROOT = Path(__file__).resolve().parents[1]


def test_scaffold_layout_exists():
    """Smoke test: services/, specs/, tests/ and the milestone runner exist."""
    assert (PLATFORM_ROOT / "services").is_dir()
    assert (PLATFORM_ROOT / "specs").is_dir()
    assert (PLATFORM_ROOT / "starter.py").is_file()


def test_milestones_defined():
    """Smoke test: the four-milestone plan is present in starter.py."""
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location(
        "grand_capstone_starter", PLATFORM_ROOT / "starter.py")
    assert spec is not None and spec.loader is not None
    starter = importlib.util.module_from_spec(spec)
    # dataclasses resolve cls.__module__ via sys.modules at class-creation time.
    sys.modules["grand_capstone_starter"] = starter
    spec.loader.exec_module(starter)
    assert [m.number for m in starter.MILESTONES] == [1, 2, 3, 4]


@pytest.mark.skip(reason="TODO: M1 — implement catalog + orders services, then unskip")
def test_m1_rest_core_contract_tests_green():
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: M2 — GraphQL read model + inventory gRPC, then unskip")
def test_m2_read_model_and_internal_rpc():
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: M3 — outbox, signed webhooks, SSE, AsyncAPI lint, then unskip")
def test_m3_async_platform():
    raise NotImplementedError


@pytest.mark.skip(reason="TODO: M4 — traces, SLOs, chaos drill, portal, then unskip")
def test_m4_production_hardening_and_chaos_drill():
    raise NotImplementedError
