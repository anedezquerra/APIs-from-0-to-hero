"""Simulation harness: replay one synthetic request timeline through every
reference limiter and print per-bucket admission counts.

The timeline is fully seeded and deterministic; re-running always prints the
same numbers. The printed coordinates are exactly the data series plotted in
Figure 14.4 (burst behavior comparison).

Scenario (Northwind Robotics telemetry ingest API, nominal plan:
10 requests/second per API key):
  * t in [0.90, 1.10]: a 25-request burst straddling the t=1.0 fixed-window
    boundary (a mobile fleet retrying in sync after a connectivity blip),
  * t in [1.50, 4.00]: a steady stream of 8 requests/second with seeded
    jitter -- well below the nominal rate, so a correct limiter should admit
    all of it after the burst penalty is paid.
"""

from __future__ import annotations

import random
from typing import Callable, Dict, List, Tuple

from rate_limiters import (
    FixedWindowLimiter,
    GCRALimiter,
    SlidingWindowCounterLimiter,
    SlidingWindowLogLimiter,
    TokenBucketLimiter,
    VirtualClock,
)

NOMINAL_RATE = 10  # requests per second per API key
WINDOW = 1.0
BUCKET_WIDTH = 0.25  # chart resolution


def build_timeline(seed: int = 14) -> List[float]:
    """Deterministic synthetic request timeline (arrival times, seconds)."""
    rng = random.Random(seed)
    arrivals: List[float] = []
    # Synchronized retry burst: 25 requests spread across the t=1.0 boundary.
    for i in range(25):
        arrivals.append(0.90 + i * 0.008 + rng.uniform(0.0, 0.002))
    # Steady-state traffic at 8 rps with jitter, from t=1.5 to t=4.0.
    t = 1.5
    while t <= 4.0:
        arrivals.append(t)
        t += 1.0 / 8.0 + rng.uniform(-0.03, 0.03)
    arrivals.sort()
    return arrivals


def simulate(arrivals: List[float],
             make_limiter: Callable[[VirtualClock], object]) -> Dict[float, int]:
    """Replay arrivals; return {bucket_start: admitted_count}."""
    clock = VirtualClock()
    limiter = make_limiter(clock)
    buckets: Dict[float, int] = {}
    for t in arrivals:
        decision = limiter.check(at=t)  # type: ignore[attr-defined]
        if decision.allowed:
            bucket = round(int(t / BUCKET_WIDTH) * BUCKET_WIDTH, 2)
            buckets[bucket] = buckets.get(bucket, 0) + 1
    return buckets


def main() -> None:
    arrivals = build_timeline()
    factories: List[Tuple[str, Callable[[VirtualClock], object]]] = [
        ("fixed window", lambda c: FixedWindowLimiter(NOMINAL_RATE, WINDOW, c)),
        ("sliding log", lambda c: SlidingWindowLogLimiter(NOMINAL_RATE, WINDOW, c)),
        ("sliding counter", lambda c: SlidingWindowCounterLimiter(NOMINAL_RATE, WINDOW, c)),
        ("token bucket", lambda c: TokenBucketLimiter(NOMINAL_RATE, NOMINAL_RATE, c)),
        ("GCRA", lambda c: GCRALimiter(NOMINAL_RATE, NOMINAL_RATE, c)),
    ]
    print(f"timeline: {len(arrivals)} arrivals, "
          f"t={arrivals[0]:.3f}..{arrivals[-1]:.3f}")
    all_starts = [round(i * BUCKET_WIDTH, 2) for i in range(int(4.0 / BUCKET_WIDTH) + 1)]
    for name, factory in factories:
        buckets = simulate(arrivals, factory)
        total = sum(buckets.values())
        coords = " ".join(f"({s:.2f}, {buckets.get(s, 0)})" for s in all_starts)
        print(f"\n{name}: admitted {total}/{len(arrivals)}")
        print(coords)


if __name__ == "__main__":
    main()
