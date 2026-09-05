"""Tests for the Redis+Lua distributed limiter (offline, fakeredis).

Atomicity note: real Redis executes each Lua script atomically on its single
command thread, so no interleaving of ZREMRANGEBYSCORE/ZCARD/ZADD is
possible across clients. fakeredis emulates the same contract in-process
(scripts run to completion under its server lock), so the concurrency test
below exercises the true atomicity semantics without a server. What fakeredis
does NOT emulate is wall-clock key expiry timing -- which is why the limiter
never relies on EXPIRE for correctness, only for memory hygiene.
"""

from __future__ import annotations

import threading

import pytest

from rate_limiters import VirtualClock
from redis_limiter import RedisSlidingLogLimiter, build_fake_limiter


class TestSemantics:
    def test_admits_limit_then_rejects(self) -> None:
        clock = VirtualClock()
        limiter = build_fake_limiter(limit=3, window=10.0, clock=clock)
        results = [limiter.check("robot-7", at=1.0).allowed for _ in range(5)]
        assert results == [True, True, True, False, False]

    def test_window_slides_exactly(self) -> None:
        clock = VirtualClock()
        limiter = build_fake_limiter(limit=2, window=10.0, clock=clock)
        limiter.check("robot-7", at=5.0)
        limiter.check("robot-7", at=7.0)
        assert not limiter.check("robot-7", at=14.999).allowed
        assert limiter.check("robot-7", at=15.0).allowed  # 5.0 has aged out

    def test_keys_are_isolated(self) -> None:
        clock = VirtualClock()
        limiter = build_fake_limiter(limit=1, window=10.0, clock=clock)
        assert limiter.check("robot-7", at=0.0).allowed
        assert limiter.check("robot-8", at=0.0).allowed
        assert not limiter.check("robot-7", at=0.0).allowed

    def test_retry_after_matches_oldest_expiry(self) -> None:
        clock = VirtualClock()
        limiter = build_fake_limiter(limit=2, window=10.0, clock=clock)
        limiter.check("robot-7", at=1.25)
        limiter.check("robot-7", at=3.00)
        decision = limiter.check("robot-7", at=4.0)
        assert not decision.allowed
        # Oldest (1.25) leaves the window at 11.25; ceil to milliseconds.
        assert decision.retry_after == pytest.approx(7.25, abs=0.001)

    def test_idle_keys_expire_from_redis(self) -> None:
        import fakeredis

        clock = VirtualClock()
        client = fakeredis.FakeRedis()
        limiter = RedisSlidingLogLimiter(client, "northwind:rl", 5, 10.0, clock)
        limiter.check("robot-7", at=0.0)
        ttl_ms = client.pttl("northwind:rl:robot-7")
        assert 9_000 < ttl_ms <= 10_000


class TestConcurrency:
    def test_no_over_admission_under_thread_storm(self) -> None:
        """16 threads x 25 requests against limit 100: exactly 100 admissions,
        never 101. A non-atomic check-then-set would intermittently fail."""
        clock = VirtualClock()
        limiter = build_fake_limiter(limit=100, window=60.0, clock=clock)
        admitted = 0
        admitted_lock = threading.Lock()

        def worker() -> None:
            nonlocal admitted
            local = 0
            for _ in range(25):
                if limiter.check("fleet-shared-key", at=0.0).allowed:
                    local += 1
            with admitted_lock:
                admitted += local

        threads = [threading.Thread(target=worker) for _ in range(16)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert admitted == 100
