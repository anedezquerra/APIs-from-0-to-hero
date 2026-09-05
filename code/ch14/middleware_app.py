"""FastAPI middleware wiring a rate limiter to client-facing HTTP semantics.

Semantics implemented (Section 14.3, "Client-Facing Semantics"):
  * per-API-key buckets, keyed on the ``X-API-Key`` header,
  * 429 Too Many Requests with ``Retry-After`` (delay-seconds form) on
    rejection,
  * IETF RateLimit header fields on every limited response:
    ``RateLimit-Limit``, ``RateLimit-Remaining``, ``RateLimit-Reset``,
    ``RateLimit-Policy`` (e.g. ``5;w=60``),
  * a fail-open / fail-closed policy switch for limiter outages.

The limiter is injected behind the ``KeyedLimiter`` protocol, so the same
middleware runs against the in-process fixed-window limiter here, or the
Redis limiter of Listing 14.4 in a multi-replica deployment. The clock is
injected, so tests are deterministic.
"""

from __future__ import annotations

import math
from typing import Dict, Literal, Optional, Protocol

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from rate_limiters import Clock, Decision, VirtualClock

FailurePolicy = Literal["fail_open", "fail_closed"]

VALID_API_KEYS = {"nr-demo-key-001", "nr-demo-key-002"}  # synthetic only


class KeyedLimiter(Protocol):
    """Anything that can admit or reject for a key and report reset time."""

    def check(self, key: str) -> Decision: ...

    def reset_after(self, key: str) -> float:
        """Seconds until the key's window fully resets (0 if idle)."""
        ...


class InProcessFixedWindowLimiter:
    """Per-key fixed-window counters with an injected clock.

    Correct O(1)-memory semantics for a single replica; subject to the
    2x boundary burst of Theorem 14.1, which is acceptable when the window
    is short and the header contract (crisp RateLimit-Reset) matters more
    than boundary strictness. Swap in RedisSlidingLogLimiter for
    multi-replica deployments.
    """

    def __init__(self, limit: int, window: float, clock: Clock) -> None:
        if limit <= 0 or window <= 0:
            raise ValueError("limit and window must be positive")
        self.limit = limit
        self.window = window
        self.clock = clock
        self._buckets: Dict[str, tuple[int, int]] = {}  # key -> (index, count)

    def check(self, key: str) -> Decision:
        t = self.clock.now()
        index = math.floor(t / self.window)
        bucket_index, count = self._buckets.get(key, (index, 0))
        if bucket_index != index:
            bucket_index, count = index, 0
        window_end = (index + 1) * self.window
        if count < self.limit:
            self._buckets[key] = (bucket_index, count + 1)
            return Decision(True, self.limit - count - 1, 0.0)
        self._buckets[key] = (bucket_index, count)
        return Decision(False, 0, window_end - t)

    def reset_after(self, key: str) -> float:
        t = self.clock.now()
        index = math.floor(t / self.window)
        bucket = self._buckets.get(key)
        if bucket is None or bucket[0] != index or bucket[1] == 0:
            return 0.0
        return (index + 1) * self.window - t


class RateLimitMiddleware:
    """ASGI middleware enforcing a per-API-key limit with full headers."""

    def __init__(
        self,
        app: FastAPI,
        limiter: KeyedLimiter,
        limit: int,
        window: float,
        on_limiter_error: FailurePolicy = "fail_open",
    ) -> None:
        if on_limiter_error not in ("fail_open", "fail_closed"):
            raise ValueError("on_limiter_error must be 'fail_open' or 'fail_closed'")
        self.app = app
        self.limiter = limiter
        self.limit = limit
        self.window = window
        self.on_limiter_error = on_limiter_error

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        api_key = request.headers.get("x-api-key")
        if api_key not in VALID_API_KEYS:
            response = JSONResponse(
                status_code=401,
                content={"detail": "missing or invalid API key"},
            )
            await response(scope, receive, send)
            return

        try:
            decision = self.limiter.check(api_key)
        except Exception:
            if self.on_limiter_error == "fail_open":
                # Limiter down: serve anyway, and say nothing we cannot
                # substantiate -- no RateLimit headers we cannot compute.
                await self.app(scope, receive, send)
                return
            response = JSONResponse(
                status_code=503,
                content={"detail": "rate limiter unavailable; failing closed"},
                headers={"Retry-After": "5"},
            )
            await response(scope, receive, send)
            return

        headers = self._ratelimit_headers(api_key, decision)
        if not decision.allowed:
            headers["Retry-After"] = str(max(1, math.ceil(decision.retry_after)))
            response = JSONResponse(
                status_code=429,
                content={"detail": "rate limit exceeded"},
                headers=headers,
            )
            await response(scope, receive, send)
            return

        async def send_with_headers(message) -> None:
            if message["type"] == "http.response.start":
                extra = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
                message["headers"] = list(message.get("headers", [])) + extra
            await send(message)

        await self.app(scope, receive, send_with_headers)

    def _ratelimit_headers(self, key: str, decision: Decision) -> Dict[str, str]:
        reset = decision.retry_after if not decision.allowed else self.limiter.reset_after(key)
        return {
            "RateLimit-Limit": str(self.limit),
            "RateLimit-Remaining": str(max(0, decision.remaining)),
            "RateLimit-Reset": str(max(0, math.ceil(reset))),
            "RateLimit-Policy": f"{self.limit};w={int(self.window)}",
        }


def create_app(
    limiter: Optional[KeyedLimiter] = None,
    clock: Optional[Clock] = None,
    on_limiter_error: FailurePolicy = "fail_open",
    limit: int = 5,
    window: float = 60.0,
) -> FastAPI:
    """Northwind Robotics telemetry API behind the rate-limit middleware."""
    clock = clock or VirtualClock()
    limiter = limiter or InProcessFixedWindowLimiter(limit, window, clock)
    app = FastAPI(title="Northwind Robotics Telemetry API")
    app.add_middleware(
        RateLimitMiddleware,
        limiter=limiter,
        limit=limit,
        window=window,
        on_limiter_error=on_limiter_error,
    )

    @app.get("/telemetry")
    def telemetry() -> dict[str, str]:
        return {"status": "ok", "fleet": "northwind-robotics"}

    return app


if __name__ == "__main__":
    demo_clock = VirtualClock()
    client = TestClient(create_app(clock=demo_clock))
    for i in range(7):
        resp = client.get("/telemetry", headers={"X-API-Key": "nr-demo-key-001"})
        interesting = {k: v for k, v in resp.headers.items()
                       if k.startswith(("ratelimit", "retry"))}
        print(f"request {i + 1}: {resp.status_code} {interesting}")
