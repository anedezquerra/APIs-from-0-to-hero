"""Deterministic unit tests for the five reference limiters.

Every test injects a VirtualClock; nothing here reads wall time. The
fixed-window double-burst flaw and the GCRA/token-bucket equivalence are
proven as executable tests, mirroring the chapter's theorems.
"""

from __future__ import annotations

import pytest

from rate_limiters import (
    FixedWindowLimiter,
    GCRALimiter,
    SlidingWindowCounterLimiter,
    SlidingWindowLogLimiter,
    TokenBucketLimiter,
    VirtualClock,
)


def run_burst(limiter, n: int, at: float) -> int:
    """Fire n requests at the same instant; return how many were admitted."""
    return sum(1 for _ in range(n) if limiter.check(at=at).allowed)


class TestFixedWindow:
    def test_admits_up_to_limit_per_window(self) -> None:
        clock = VirtualClock()
        limiter = FixedWindowLimiter(limit=3, window=10.0, clock=clock)
        assert run_burst(limiter, 3, at=1.0) == 3
        assert not limiter.check(at=2.0).allowed
        assert not limiter.check(at=9.9).allowed
        # A fresh window restores the full quota.
        assert limiter.check(at=10.0).allowed

    def test_double_burst_at_boundary(self) -> None:
        """Executable proof of Theorem 14.1: a fixed-window limiter configured
        for N per W admits up to 2N requests inside a single real-time
        interval of length W that straddles a boundary."""
        clock = VirtualClock()
        limiter = FixedWindowLimiter(limit=10, window=1.0, clock=clock)
        admitted = 0
        # 10 requests at the very end of window 0 ...
        admitted += run_burst(limiter, 10, at=0.999)
        # ... and 10 more at the very start of window 1. Both windows admit
        # their full quota, yet all 20 requests fall inside [0.999, 1.001],
        # a real interval of 2 ms -- far shorter than the nominal window.
        admitted += run_burst(limiter, 10, at=1.001)
        assert admitted == 20  # 2x the nominal limit
        assert 1.001 - 0.999 < 1.0


class TestSlidingWindowLog:
    def test_exactness(self) -> None:
        clock = VirtualClock()
        limiter = SlidingWindowLogLimiter(limit=3, window=10.0, clock=clock)
        # Three requests mid-window saturate it; crossing the fixed
        # boundary at t=10 does NOT restore quota, because the window
        # slides with the caller.
        assert run_burst(limiter, 5, at=5.0) == 3
        assert run_burst(limiter, 5, at=10.0) == 0
        assert run_burst(limiter, 5, at=14.999) == 0
        # At t=15.0 the first request has fully aged out.
        assert limiter.check(at=15.0).allowed

    def test_no_interval_exceeds_limit(self) -> None:
        """For any request pattern, the admitted set never contains more
        than ``limit`` events inside any half-open interval of length
        ``window``: the (i + limit)-th admission is always strictly more
        than ``window`` after the i-th."""
        clock = VirtualClock()
        limiter = SlidingWindowLogLimiter(limit=4, window=2.0, clock=clock)
        admitted: list[float] = []
        t = 0.0
        for _ in range(400):
            t += 0.05
            if limiter.check(at=t).allowed:
                admitted.append(t)
        for i in range(len(admitted) - 4):
            assert admitted[i + 4] - admitted[i] > 2.0 - 1e-9

    def test_retry_after_points_at_oldest_expiry(self) -> None:
        clock = VirtualClock()
        limiter = SlidingWindowLogLimiter(limit=2, window=10.0, clock=clock)
        limiter.check(at=1.0)
        limiter.check(at=3.0)
        decision = limiter.check(at=4.0)
        assert not decision.allowed
        assert decision.retry_after == pytest.approx(7.0)  # 1.0 + 10.0 - 4.0


class TestSlidingWindowCounter:
    def test_matches_exact_when_previous_window_empty(self) -> None:
        clock = VirtualClock()
        limiter = SlidingWindowCounterLimiter(limit=3, window=10.0, clock=clock)
        assert run_burst(limiter, 5, at=15.0) == 3

    def test_weights_previous_window_by_elapsed_fraction(self) -> None:
        clock = VirtualClock()
        limiter = SlidingWindowCounterLimiter(limit=10, window=1.0, clock=clock)
        # Saturate window 0 entirely at its start.
        assert run_burst(limiter, 10, at=0.01) == 10
        # Halfway through window 1 the estimate is 0 + 10 * (1 - 0.5) = 5,
        # so exactly 5 more requests are admitted before t = 1.5.
        assert run_burst(limiter, 10, at=1.5) == 5

    def test_error_bound_holds(self) -> None:
        """Executable check of Proposition 14.2: the absolute error of the
        weighted estimate is strictly less than the previous window count."""
        clock = VirtualClock()
        counter = SlidingWindowCounterLimiter(limit=8, window=1.0, clock=clock)
        exact = SlidingWindowLogLimiter(limit=8, window=1.0, clock=clock)
        # Adversarial: all of window 0's traffic bunched at its very end.
        run_burst(counter, 8, at=0.99)
        run_burst(exact, 8, at=0.99)
        admitted_counter = run_burst(counter, 20, at=1.01)
        admitted_exact = run_burst(exact, 20, at=1.01)
        # The exact log admits 0 here (all 8 requests still inside the
        # sliding window); the counter over-admits 1 because it assumes
        # window-0 traffic was spread uniformly. Error 1 < previous
        # window count 8, as the bound predicts.
        assert admitted_exact == 0
        assert admitted_counter == 1
        assert abs(admitted_counter - admitted_exact) < 8


class TestTokenBucket:
    def test_burst_equals_capacity(self) -> None:
        clock = VirtualClock()
        limiter = TokenBucketLimiter(rate=10.0, burst=10, clock=clock)
        assert run_burst(limiter, 100, at=0.0) == 10
        # Half a second of silence refills exactly five tokens.
        clock.advance(0.5)
        assert run_burst(limiter, 100, at=clock.now()) == 5

    def test_long_run_rate_never_exceeds_refill(self) -> None:
        """Executable check of Proposition 14.3: over any interval [t0, t1]
        the admitted count is at most burst + rate * (t1 - t0)."""
        clock = VirtualClock()
        limiter = TokenBucketLimiter(rate=10.0, burst=10, clock=clock)
        admitted = 0
        t = 0.0
        for _ in range(2000):
            t += 0.02
            if limiter.check(at=t).allowed:
                admitted += 1
        assert admitted <= 10 + 10.0 * t + 1e-9

    def test_retry_after_is_deficit_over_rate(self) -> None:
        clock = VirtualClock()
        limiter = TokenBucketLimiter(rate=4.0, burst=2, clock=clock)
        run_burst(limiter, 2, at=0.0)
        decision = limiter.check(at=0.0)
        assert not decision.allowed
        assert decision.retry_after == pytest.approx(0.25)


class TestGCRA:
    def test_equivalent_to_token_bucket(self) -> None:
        """GCRA with emission interval T and tolerance tau = (B-1)T admits
        exactly the same streams as a token bucket with capacity B and rate
        1/T. Proven by construction in Section 14.3 (GCRA); checked here on a
        seeded adversarial stream."""
        import random

        rng = random.Random(14)
        gcra = GCRALimiter(rate=10.0, burst=10, clock=VirtualClock())
        bucket = TokenBucketLimiter(rate=10.0, burst=10, clock=VirtualClock())
        t = 0.0
        for _ in range(500):
            t += rng.choice([0.0, 0.005, 0.02, 0.2, 1.0])
            assert gcra.check(at=t).allowed == bucket.check(at=t).allowed

    def test_steady_stream_at_rate_always_conforms(self) -> None:
        clock = VirtualClock()
        limiter = GCRALimiter(rate=5.0, burst=3, clock=clock)
        for i in range(100):
            assert limiter.check(at=i * 0.2).allowed

    def test_retry_after_is_tat_minus_tolerance_minus_now(self) -> None:
        clock = VirtualClock()
        limiter = GCRALimiter(rate=10.0, burst=2, clock=clock)  # T=0.1, tau=0.1
        assert limiter.check(at=0.0).allowed   # TAT: 0.1
        assert limiter.check(at=0.0).allowed   # TAT: 0.2
        decision = limiter.check(at=0.0)       # arrival limit = 0.2 - 0.1
        assert not decision.allowed
        assert decision.retry_after == pytest.approx(0.1)
