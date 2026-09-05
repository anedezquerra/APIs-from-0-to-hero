"""Tests for the mini OpenAPI fuzzer.

Run:  pytest test_fuzz_openapi_mini.py -q
"""
from __future__ import annotations

import httpx

from fuzz_openapi_mini import REQUEST_SCHEMA, fuzz_cases, run_fuzz, shrink
from robot_registry import create_app, make_sync_client


def _client(**app_kwargs: object) -> httpx.Client:
    return make_sync_client(
        create_app(**app_kwargs),  # type: ignore[arg-type]
        base_url="http://fuzz.test",
    )


def test_fuzzer_finds_no_failures_on_healthy_app() -> None:
    cases = fuzz_cases(REQUEST_SCHEMA)
    total, failures = run_fuzz(_client(), cases)
    assert total == len(cases) and total > 30  # report hygiene: prove coverage
    assert failures == [], [f"{f.label}: {f.reason}" for f in failures]


def test_fuzzer_finds_and_shrinks_the_planted_bug() -> None:
    cases = fuzz_cases(REQUEST_SCHEMA)
    client = _client(bug_at_price=666)
    _, failures = run_fuzz(client, cases)
    assert failures, "fuzzer must find the planted 500"
    assert all(f.status == 500 for f in failures)
    first = failures[0]
    minimal = shrink(client, first.payload, lambda r: r.status_code >= 500, REQUEST_SCHEMA)
    # Required keys cannot be dropped (that flips 500 -> 422), so the minimal
    # reproducer isolates the trigger field with minimal valid stand-ins:
    assert minimal == {"sku": "AAA", "name": "A", "price_cents": 666}


def test_every_4xx_is_problem_shaped() -> None:
    """A focused regression of the RFC 9457 invariant on the healthy app."""
    cases = fuzz_cases(REQUEST_SCHEMA)
    client = _client()
    saw_4xx = 0
    for label, payload in cases:
        resp = client.post("/robots", json=payload)
        if 400 <= resp.status_code < 500:
            saw_4xx += 1
            body = resp.json()
            assert body["status"] == resp.status_code, label
            assert resp.headers["content-type"].startswith("application/problem+json")
    assert saw_4xx > 10  # the fuzzer really exercised the validation boundary
