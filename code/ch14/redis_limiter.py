"""Distributed sliding-window limiter: Redis sorted set + Lua script.

State lives in Redis so any number of API replicas enforce one shared limit
per key. The whole check-and-admit operation is a single Lua script, so it
executes atomically on the Redis server: no read-modify-write race can split
it, no matter how many replicas call concurrently.

Offline-first: tests run against ``fakeredis.FakeRedis``, which emulates
RESP and executes Lua scripts atomically inside the process, so the same
code paths are exercised without a server. For a real deployment swap in
``redis.Redis`` (redis>=5) -- the script and calling convention are
identical.
"""

from __future__ import annotations

import itertools
import threading
from typing import Optional, Protocol

from rate_limiters import Clock, Decision, VirtualClock


class RedisLike(Protocol):
    """The subset of the redis-py API this limiter needs."""

    def eval(self, script: str, numkeys: int, *keys_and_args: object) -> object: ...


# Sliding-window log as one atomic Lua script (also printed standalone as
# Listing 14.4a; it lives inline here so this file is complete and runnable).
SLIDING_WINDOW_LUA = """
local key     = KEYS[1]
local now     = tonumber(ARGV[1])
local window  = tonumber(ARGV[2])
local limit   = tonumber(ARGV[3])
local member  = ARGV[4]

redis.call('ZREMRANGEBYSCORE', key, '-inf', now - window)
local count = redis.call('ZCARD', key)

if count < limit then
  redis.call('ZADD', key, now, member)
  redis.call('PEXPIRE', key, math.ceil(window * 1000))
  return {1, limit - count - 1, 0}
else
  -- ZRANGE + ZSCORE (not WITHSCORES): the WITHSCORES return shape inside
  -- Lua differs between Redis and emulators; two calls are portable.
  local oldest = redis.call('ZRANGE', key, 0, 0)
  local retry_after_ms = 0
  if #oldest >= 1 then
    local score = tonumber(redis.call('ZSCORE', key, oldest[1]))
    retry_after_ms = math.ceil((score + window - now) * 1000)
  end
  return {0, 0, retry_after_ms}
end
"""


class RedisSlidingLogLimiter:
    """Shared sliding-window-log limiter backed by Redis sorted sets.

    Semantics match ``SlidingWindowLogLimiter`` exactly: at most ``limit``
    admissions per key inside any interval of ``window`` seconds. One Redis
    key per (namespace, limiter key) pair; keys self-expire after ``window``
    so idle consumers cost no memory.
    """

    def __init__(
        self,
        client: RedisLike,
        namespace: str,
        limit: int,
        window: float,
        clock: Clock,
    ) -> None:
        if limit <= 0 or window <= 0:
            raise ValueError("limit and window must be positive")
        if not namespace:
            raise ValueError("namespace must be non-empty")
        self.client = client
        self.namespace = namespace
        self.limit = limit
        self.window = float(window)
        self.clock = clock
        self._seq = itertools.count()
        self._seq_lock = threading.Lock()

    def _member(self, t: float) -> str:
        # ZADD upserts by member, so every admitted request needs a unique
        # member id; identical scores are fine.
        with self._seq_lock:
            return f"{t:.6f}:{next(self._seq)}"

    def check(self, key: str, at: Optional[float] = None) -> Decision:
        if not key:
            raise ValueError("limiter key must be non-empty")
        t = self.clock.now() if at is None else at
        redis_key = f"{self.namespace}:{key}"
        raw = self.client.eval(
            SLIDING_WINDOW_LUA,
            1,
            redis_key,
            repr(t),
            repr(self.window),
            str(self.limit),
            self._member(t),
        )
        allowed, remaining, retry_after_ms = (int(v) for v in raw)
        return Decision(bool(allowed), remaining, retry_after_ms / 1000.0)


def build_fake_limiter(
    limit: int = 5, window: float = 10.0, clock: Optional[Clock] = None
) -> RedisSlidingLogLimiter:
    """Offline factory: a limiter against an in-process fakeredis server."""
    import fakeredis

    return RedisSlidingLogLimiter(
        client=fakeredis.FakeRedis(),
        namespace="northwind:rl",
        limit=limit,
        window=window,
        clock=clock or VirtualClock(),
    )
