"""Reference implementations of the five classic rate-limiting algorithms.

Every limiter takes an injected ``Clock`` so behavior is fully deterministic
under test: no wall-clock reads anywhere. Time is in float seconds.

Algorithms implemented:
  * FixedWindowLimiter      -- counter per floor(t / window) bucket
  * SlidingWindowLogLimiter -- exact timestamp log
  * SlidingWindowCounterLimiter -- weighted previous/current window estimate
  * TokenBucketLimiter      -- capacity B, refill rate r
  * GCRALimiter             -- generic cell rate algorithm (leaky bucket as
                               a meter), parameterized by emission interval T
                               and burst tolerance tau

All limiters expose the same ``allow(at=None) -> bool`` contract and are
single-process reference models; Listing 14.4 lifts the sliding log to Redis.
"""

from __future__ import annotations

import math
from collections import deque
from typing import Deque, Optional, Protocol


class Clock(Protocol):
    """Anything that reports the current time in float seconds."""

    def now(self) -> float: ...


class VirtualClock:
    """Deterministic, manually advanced clock for tests and simulations."""

    def __init__(self, start: float = 0.0) -> None:
        self._t = float(start)

    def now(self) -> float:
        return self._t

    def advance(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("cannot move a clock backwards")
        self._t += seconds


class Decision:
    """Result of an admission check: admit flag plus header metadata."""

    def __init__(self, allowed: bool, remaining: int, retry_after: float) -> None:
        self.allowed = allowed
        self.remaining = remaining
        self.retry_after = max(0.0, retry_after)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"Decision(allowed={self.allowed}, remaining={self.remaining}, "
            f"retry_after={self.retry_after:.3f})"
        )


class FixedWindowLimiter:
    """Allow at most ``limit`` requests per fixed window of ``window`` seconds.

    Memory: O(1). Flaw: up to ``2 * limit`` requests can be admitted inside
    any real-time interval of length ``window`` (see Theorem 14.1).
    """

    def __init__(self, limit: int, window: float, clock: Clock) -> None:
        if limit <= 0 or window <= 0:
            raise ValueError("limit and window must be positive")
        self.limit = limit
        self.window = window
        self.clock = clock
        self._window_index = -1
        self._count = 0

    def check(self, at: Optional[float] = None) -> Decision:
        t = self.clock.now() if at is None else at
        index = math.floor(t / self.window)
        if index != self._window_index:
            self._window_index = index
            self._count = 0
        window_end = (index + 1) * self.window
        if self._count < self.limit:
            self._count += 1
            return Decision(True, self.limit - self._count, 0.0)
        return Decision(False, 0, window_end - t)


class SlidingWindowLogLimiter:
    """Exact limiter: keep the timestamp of every admitted request.

    Memory: O(limit) per key. Never admits more than ``limit`` requests in
    any interval of length ``window`` -- the gold standard for correctness.
    """

    def __init__(self, limit: int, window: float, clock: Clock) -> None:
        if limit <= 0 or window <= 0:
            raise ValueError("limit and window must be positive")
        self.limit = limit
        self.window = window
        self.clock = clock
        self._log: Deque[float] = deque()

    def check(self, at: Optional[float] = None) -> Decision:
        t = self.clock.now() if at is None else at
        cutoff = t - self.window
        while self._log and self._log[0] <= cutoff:
            self._log.popleft()
        if len(self._log) < self.limit:
            self._log.append(t)
            return Decision(True, self.limit - len(self._log), 0.0)
        oldest = self._log[0]
        return Decision(False, 0, oldest + self.window - t)


class SlidingWindowCounterLimiter:
    """Weighted approximation of the sliding log with O(1) memory.

    Estimate for the true count in [t - window, t]:
        estimate = current + previous * (1 - elapsed_fraction)
    where elapsed_fraction is how far ``t`` has progressed into the current
    fixed window. The absolute error versus the exact log is strictly less
    than the previous window's count (Proposition 14.2).
    """

    def __init__(self, limit: int, window: float, clock: Clock) -> None:
        if limit <= 0 or window <= 0:
            raise ValueError("limit and window must be positive")
        self.limit = limit
        self.window = window
        self.clock = clock
        self._prev_index = -1
        self._prev_count = 0
        self._curr_index = -1
        self._curr_count = 0

    def check(self, at: Optional[float] = None) -> Decision:
        t = self.clock.now() if at is None else at
        index = math.floor(t / self.window)
        if index != self._curr_index:
            self._prev_index = self._curr_index
            self._prev_count = self._curr_count if self._curr_index == index - 1 else 0
            self._curr_index = index
            self._curr_count = 0
        elapsed_fraction = (t - index * self.window) / self.window
        previous = self._prev_count if self._prev_index == index - 1 else 0
        estimate = self._curr_count + previous * (1.0 - elapsed_fraction)
        window_end = (index + 1) * self.window
        if estimate < self.limit:
            self._curr_count += 1
            return Decision(True, max(0, int(self.limit - estimate - 1)), 0.0)
        return Decision(False, 0, window_end - t)


class TokenBucketLimiter:
    """Token bucket: capacity ``burst`` tokens, refilled at ``rate`` per second.

    Bursts up to ``burst`` are admitted instantly; the long-run admitted rate
    never exceeds ``rate`` (Proposition 14.3).
    """

    def __init__(self, rate: float, burst: float, clock: Clock) -> None:
        if rate <= 0 or burst <= 0:
            raise ValueError("rate and burst must be positive")
        self.rate = rate
        self.burst = burst
        self.clock = clock
        self._tokens = float(burst)
        self._last = clock.now()

    def _refill(self, t: float) -> None:
        if t < self._last:
            raise ValueError("timestamps must be non-decreasing")
        self._tokens = min(self.burst, self._tokens + (t - self._last) * self.rate)
        self._last = t

    def check(self, at: Optional[float] = None, cost: float = 1.0) -> Decision:
        if cost <= 0:
            raise ValueError("cost must be positive")
        t = self.clock.now() if at is None else at
        self._refill(t)
        if self._tokens >= cost:
            self._tokens -= cost
            return Decision(True, int(self._tokens), 0.0)
        deficit = cost - self._tokens
        return Decision(False, int(self._tokens), deficit / self.rate)


class GCRALimiter:
    """Generic Cell Rate Algorithm (leaky bucket used as a meter).

    Parameters: ``rate`` requests per second sustained, ``burst`` requests
    tolerated instantly. Emission interval T = 1 / rate; burst tolerance
    tau = (burst - 1) * T. State is a single timestamp: the theoretical
    arrival time (TAT) of the next conforming request.
    """

    def __init__(self, rate: float, burst: int, clock: Clock) -> None:
        if rate <= 0 or burst <= 0:
            raise ValueError("rate and burst must be positive")
        self.rate = float(rate)
        self.emission_interval = 1.0 / rate  # T
        self.tolerance = (burst - 1) * self.emission_interval  # tau
        self.clock = clock
        self._tat = float("-inf")

    def check(self, at: Optional[float] = None) -> Decision:
        t = self.clock.now() if at is None else at
        arrival_limit = self._tat - self.tolerance
        if t < arrival_limit:
            return Decision(False, 0, arrival_limit - t)
        self._tat = max(t, self._tat) + self.emission_interval
        # Remaining burst: admits still possible right now before the
        # not-before time t >= TAT - tau would be violated.
        headroom = t + self.tolerance - self._tat
        remaining = 1 + int(headroom // self.emission_interval) if headroom >= 0 else 0
        return Decision(True, remaining, 0.0)
