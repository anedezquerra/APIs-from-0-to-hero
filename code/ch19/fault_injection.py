"""Deterministic fault-injection middleware and a resilient client transport.

Fault classes (see the chapter's fault taxonomy):

* ``LATENCY`` -- sleep (on a *virtual* clock) before calling the app;
* ``ERROR``   -- answer directly with an RFC 9457-shaped 5xx;
* ``ABORT``   -- drop the connection (raise before any response).

The :class:`VirtualClock` sleeper never waits in real time: tests exercise
multi-second retry backoffs in microseconds and assert on *recorded*
virtual delays, never on the wall clock.

The :class:`ResilientTransport` is the client under test: bounded retries
with exponential backoff plus a circuit breaker that fails fast after
``breaker_threshold`` consecutive exhausted calls.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Awaitable, Callable, Sequence

import httpx

Sleeper = Callable[[float], Awaitable[None]]


class FaultKind(StrEnum):
    LATENCY = "latency"
    ERROR = "error"
    ABORT = "abort"


@dataclass(frozen=True)
class Fault:
    kind: FaultKind
    delay_ms: int = 0
    status: int = 503


class FaultScript:
    """Deterministic fault schedule: ``fault_for(i)`` depends only on the
    request index ``i``; beyond the script the service is healthy."""

    def __init__(self, entries: Sequence[Fault | None]) -> None:
        self._entries = list(entries)

    def fault_for(self, index: int) -> Fault | None:
        return self._entries[index] if index < len(self._entries) else None


class FaultInjectionMiddleware:
    """Pure ASGI middleware applying the scripted fault per request."""

    def __init__(self, app: Any, script: FaultScript, sleeper: Sleeper) -> None:
        self._app = app
        self._script = script
        self._sleeper = sleeper
        self.requests_seen = 0

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        fault = self._script.fault_for(self.requests_seen)
        self.requests_seen += 1
        if fault is None or fault.kind is FaultKind.LATENCY:
            if fault is not None:
                await self._sleeper(fault.delay_ms / 1_000.0)
            await self._app(scope, receive, send)
            return
        if fault.kind is FaultKind.ERROR:
            body = (
                b'{"type":"https://northwind-robotics.example/problems/injected",'
                b'"title":"Injected failure","status":%d,'
                b'"detail":"chaos middleware","instance":"%s"}'
                % (fault.status, scope.get("path", "/").encode())
            )
            await send({
                "type": "http.response.start",
                "status": fault.status,
                "headers": [(b"content-type", b"application/problem+json")],
            })
            await send({"type": "http.response.body", "body": body})
            return
        raise ConnectionResetError("injected abort")  # FaultKind.ABORT


class VirtualClock:
    """Sleeper that never waits: records delays, advances virtual time."""

    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


class BreakerOpenError(httpx.TransportError):
    """Raised when the circuit breaker short-circuits a call."""


@dataclass(frozen=True)
class RetryPolicy:
    retries: int = 3
    base_backoff_s: float = 0.1
    breaker_threshold: int = 3


class ResilientTransport(httpx.AsyncBaseTransport):
    """Bounded retries with virtual-clock backoff + circuit breaker."""

    def __init__(
        self,
        inner: httpx.AsyncBaseTransport,
        policy: RetryPolicy | None = None,
        sleeper: Sleeper | None = None,
    ) -> None:
        self._inner = inner
        self._policy = policy or RetryPolicy()
        self._sleeper = sleeper or _real_sleep
        self._consecutive_failures = 0

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        if self._consecutive_failures >= self._policy.breaker_threshold:
            raise BreakerOpenError("circuit breaker open: failing fast")
        policy = self._policy
        last_resp: httpx.Response | None = None
        last_exc: Exception | None = None
        for attempt in range(policy.retries + 1):
            try:
                resp = await self._inner.handle_async_request(request)
            except (httpx.TransportError, OSError) as exc:
                last_exc, resp = exc, None  # ABORT class: no response at all
            if resp is not None and resp.status_code < 500:
                self._consecutive_failures = 0
                return resp
            if resp is not None:
                await resp.aread()
                last_resp = resp
            if attempt < policy.retries:
                await self._sleeper(policy.base_backoff_s * (2**attempt))
        self._consecutive_failures += 1
        if last_resp is not None:
            return last_resp
        assert last_exc is not None
        raise last_exc


async def _real_sleep(seconds: float) -> None:
    import asyncio

    await asyncio.sleep(seconds)
