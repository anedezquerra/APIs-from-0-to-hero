"""Cost-based (weighted) rate limiting: one token bucket per API key, with
each endpoint charging a weight proportional to its true server-side cost.

A flat "requests per minute" limit treats a ``GET /health`` and a
``POST /reports/export`` as equal, but the export scans and renders a
million-row dataset while the health check is a no-op. Weighted buckets make
the budget denominated in *work*, not in *requests*: expensive operations
drain the shared budget faster, free endpoints (health probes) are never
throttled, and cheap endpoints survive exactly as long as any budget
remains.

Northwind Robotics cost table: weights are server CPU-millisecond estimates
from the Chapter 18 observability pipeline, normalized so the median read
endpoint costs 1.0.
"""

from __future__ import annotations

from typing import Dict, Optional

from rate_limiters import Clock, Decision, TokenBucketLimiter, VirtualClock

# path -> token cost per call (normalized work units)
ENDPOINT_COSTS: Dict[str, float] = {
    "/health": 0.0,          # liveness probe: never throttle
    "/telemetry": 1.0,       # median read
    "/fleet/status": 1.0,    # median read
    "/telemetry/batch": 4.0, # bulk ingest: 4x a single write
    "/reports/export": 10.0, # full-fleet CSV render: the expensive one
}
DEFAULT_COST = 1.0


class CostBasedLimiter:
    """Per-key token buckets charged by endpoint weight.

    Budget semantics: ``rate`` work-units per second sustained, ``burst``
    work-units of instantaneous headroom. With rate=10 and burst=20, a key
    may run 2 exports instantly (20 / 10) or 20 median reads, or any mix
    whose total weight fits the bucket.
    """

    def __init__(self, rate: float, burst: float, clock: Clock,
                 costs: Optional[Dict[str, float]] = None) -> None:
        if rate <= 0 or burst <= 0:
            raise ValueError("rate and burst must be positive")
        self.rate = rate
        self.burst = burst
        self.clock = clock
        self.costs = dict(ENDPOINT_COSTS if costs is None else costs)
        self._buckets: Dict[str, TokenBucketLimiter] = {}

    def cost_of(self, path: str) -> float:
        return self.costs.get(path, DEFAULT_COST)

    def check(self, key: str, path: str, at: Optional[float] = None) -> Decision:
        if not key:
            raise ValueError("limiter key must be non-empty")
        cost = self.cost_of(path)
        if cost == 0.0:
            return Decision(True, self.limit_placeholder(), 0.0)
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = TokenBucketLimiter(self.rate, self.burst, self.clock)
            self._buckets[key] = bucket
        return bucket.check(at=at, cost=cost)

    def limit_placeholder(self) -> int:
        # Free endpoints have no meaningful "remaining"; report the burst
        # budget so header math stays well-formed.
        return int(self.burst)


if __name__ == "__main__":
    clock = VirtualClock()
    limiter = CostBasedLimiter(rate=10.0, burst=20.0, clock=clock)
    key = "nr-demo-key-001"
    for path in ("/reports/export", "/reports/export", "/reports/export",
                 "/telemetry", "/telemetry", "/health"):
        d = limiter.check(key, path)
        verdict = "admitted" if d.allowed else f"rejected (retry in {d.retry_after:.1f}s)"
        print(f"{path:<18} cost={limiter.cost_of(path):>4} -> {verdict}")
