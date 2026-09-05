"""TestClient tests: header accuracy across window boundaries, 429 +
Retry-After, and the fail-open / fail-closed policy switch. All offline,
all deterministic (injected VirtualClock).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from middleware_app import create_app
from rate_limiters import Decision, VirtualClock

KEY = {"X-API-Key": "nr-demo-key-001"}
OTHER_KEY = {"X-API-Key": "nr-demo-key-002"}


@pytest.fixture()
def rig() -> tuple[TestClient, VirtualClock]:
    clock = VirtualClock(start=0.0)
    app = create_app(clock=clock, limit=5, window=60.0)
    return TestClient(app), clock


class TestHeaderAccuracy:
    def test_limit_remaining_and_policy_on_success(self, rig) -> None:
        client, _ = rig
        for expected_remaining in (4, 3, 2, 1, 0):
            resp = client.get("/telemetry", headers=KEY)
            assert resp.status_code == 200
            assert resp.headers["RateLimit-Limit"] == "5"
            assert resp.headers["RateLimit-Remaining"] == str(expected_remaining)
            assert resp.headers["RateLimit-Policy"] == "5;w=60"

    def test_reset_counts_down_to_window_end(self, rig) -> None:
        client, clock = rig
        resp = client.get("/telemetry", headers=KEY)
        assert resp.headers["RateLimit-Reset"] == "60"
        clock.advance(25.0)
        resp = client.get("/telemetry", headers=KEY)
        assert resp.headers["RateLimit-Reset"] == "35"  # 60 - 25

    def test_429_carries_retry_after_and_zero_remaining(self, rig) -> None:
        client, clock = rig
        for _ in range(5):
            assert client.get("/telemetry", headers=KEY).status_code == 200
        clock.advance(10.5)  # 49.5s until window end
        resp = client.get("/telemetry", headers=KEY)
        assert resp.status_code == 429
        assert resp.headers["Retry-After"] == "50"  # ceil(49.5)
        assert resp.headers["RateLimit-Remaining"] == "0"
        assert resp.headers["RateLimit-Reset"] == "50"

    def test_headers_reset_across_window_boundary(self, rig) -> None:
        client, clock = rig
        for _ in range(5):
            client.get("/telemetry", headers=KEY)
        assert client.get("/telemetry", headers=KEY).status_code == 429
        clock.advance(60.0)  # cross the boundary at t=60
        resp = client.get("/telemetry", headers=KEY)
        assert resp.status_code == 200
        assert resp.headers["RateLimit-Remaining"] == "4"
        assert resp.headers["RateLimit-Reset"] == "60"

    def test_buckets_are_per_api_key(self, rig) -> None:
        client, _ = rig
        for _ in range(5):
            client.get("/telemetry", headers=KEY)
        assert client.get("/telemetry", headers=KEY).status_code == 429
        resp = client.get("/telemetry", headers=OTHER_KEY)
        assert resp.status_code == 200
        assert resp.headers["RateLimit-Remaining"] == "4"

    def test_missing_key_is_401_not_429(self, rig) -> None:
        client, _ = rig
        resp = client.get("/telemetry")
        assert resp.status_code == 401
        assert "RateLimit-Limit" not in resp.headers


class BrokenLimiter:
    """A limiter that is down: every check raises, like a lost Redis."""

    def check(self, key: str) -> Decision:
        raise ConnectionError("redis: connection refused")

    def reset_after(self, key: str) -> float:
        raise ConnectionError("redis: connection refused")


class TestFailurePolicy:
    def test_fail_open_serves_without_unverifiable_headers(self) -> None:
        app = create_app(limiter=BrokenLimiter(), on_limiter_error="fail_open")
        client = TestClient(app)
        resp = client.get("/telemetry", headers=KEY)
        assert resp.status_code == 200
        assert "RateLimit-Remaining" not in resp.headers

    def test_fail_closed_returns_503_with_retry_after(self) -> None:
        app = create_app(limiter=BrokenLimiter(), on_limiter_error="fail_closed")
        client = TestClient(app)
        resp = client.get("/telemetry", headers=KEY)
        assert resp.status_code == 503
        assert resp.headers["Retry-After"] == "5"
