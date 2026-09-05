"""Smoke tests for the Capstone 2.1 scaffold — these pass out of the box.

Skipped tests are TODOs: implement the matching behavior in starter.py,
then unskip and flesh out the assertions (use httpx.MockTransport; the
suite must pass with the stub stopped).
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
    assert parser.parse_args(["--max-bytes", "10"]).max_bytes == 10


def test_main_dry_run_exits_zero():
    assert starter.main(["--dry-run"]) == starter.EXIT_OK


@pytest.mark.skip(reason="TODO: implement build_client, then unskip")
def test_client_has_explicit_four_dimension_timeouts():
    client = starter.build_client()
    timeout = client.timeout
    assert all(getattr(timeout, f) is not None for f in ("connect", "read", "write", "pool"))


@pytest.mark.skip(reason="TODO: implement download, then unskip")
def test_failed_download_leaves_no_partial_artifact(tmp_path):
    plan = starter.DownloadPlan(url="http://stub/catalog/export",
                                output=tmp_path / "out.ndjson", max_bytes=None)
    with pytest.raises(starter.DownloadError):
        starter.download(plan)  # against a MockTransport that fails mid-stream
    assert not plan.output.exists()
    assert not plan.output.with_suffix(".part").exists()


@pytest.mark.skip(reason="TODO: implement download, then unskip")
def test_mock_transport_matrix_200_404_500_then_200_malformed():
    # TODO: cover 200, 404 (EXIT_CLIENT_ERROR), 500-then-200 (bounded retry),
    # and a malformed body; assert exit codes per the README contract.
    raise NotImplementedError
