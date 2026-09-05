"""Tests for the cost-based limiter: weighted drainage, free endpoints,
default costs, and graceful degradation of cheap endpoints under budget
pressure. Deterministic via VirtualClock.
"""

from __future__ import annotations

import pytest

from cost_limiter import CostBasedLimiter
from rate_limiters import VirtualClock

KEY = "nr-demo-key-001"


@pytest.fixture()
def limiter() -> CostBasedLimiter:
    return CostBasedLimiter(rate=10.0, burst=20.0, clock=VirtualClock())


class TestWeightedDrainage:
    def test_export_costs_ten_reads(self, limiter: CostBasedLimiter) -> None:
        # Two exports (2 x 10 units) exactly exhaust a 20-unit bucket.
        assert limiter.check(KEY, "/reports/export", at=0.0).allowed
        assert limiter.check(KEY, "/reports/export", at=0.0).allowed
        assert not limiter.check(KEY, "/reports/export", at=0.0).allowed

    def test_mixed_workload_shares_one_budget(self, limiter: CostBasedLimiter) -> None:
        assert limiter.check(KEY, "/reports/export", at=0.0).allowed  # 10
        for _ in range(10):
            assert limiter.check(KEY, "/telemetry", at=0.0).allowed   # 10 x 1
        assert not limiter.check(KEY, "/telemetry", at=0.0).allowed   # 21st unit

    def test_refill_is_in_work_units(self, limiter: CostBasedLimiter) -> None:
        limiter.check(KEY, "/reports/export", at=0.0)
        limiter.check(KEY, "/reports/export", at=0.0)
        # 1.0s of refill = 10 work units = exactly one more export.
        assert limiter.check(KEY, "/reports/export", at=1.0).allowed
        assert not limiter.check(KEY, "/reports/export", at=1.0).allowed

    def test_retry_after_scales_with_cost(self, limiter: CostBasedLimiter) -> None:
        limiter.check(KEY, "/reports/export", at=0.0)
        limiter.check(KEY, "/reports/export", at=0.0)
        cheap = limiter.check(KEY, "/telemetry", at=0.0)
        dear = limiter.check(KEY, "/reports/export", at=0.0)
        assert cheap.retry_after == pytest.approx(0.1)   # 1 unit / 10 rps
        assert dear.retry_after == pytest.approx(1.0)    # 10 units / 10 rps


class TestEdgeCases:
    def test_health_endpoint_is_never_throttled(self, limiter: CostBasedLimiter) -> None:
        for _ in range(2):
            limiter.check(KEY, "/reports/export", at=0.0)
        for _ in range(100):
            assert limiter.check(KEY, "/health", at=0.0).allowed

    def test_unknown_path_defaults_to_unit_cost(self, limiter: CostBasedLimiter) -> None:
        assert limiter.cost_of("/no/such/route") == 1.0
        for i in range(20):
            assert limiter.check(KEY, "/no/such/route", at=0.0).allowed, i
        assert not limiter.check(KEY, "/no/such/route", at=0.0).allowed

    def test_budgets_are_per_key(self, limiter: CostBasedLimiter) -> None:
        limiter.check(KEY, "/reports/export", at=0.0)
        limiter.check(KEY, "/reports/export", at=0.0)
        assert not limiter.check(KEY, "/reports/export", at=0.0).allowed
        assert limiter.check("nr-demo-key-002", "/reports/export", at=0.0).allowed
