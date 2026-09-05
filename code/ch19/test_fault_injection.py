"""Deterministic resilience tests: every fault class, zero wall-clock waits.

Run:  pytest test_fault_injection.py -q
"""
from __future__ import annotations

import asyncio

import httpx
import pytest

from fault_injection import (
    BreakerOpenError,
    Fault,
    FaultInjectionMiddleware,
    FaultKind,
    FaultScript,
    ResilientTransport,
    RetryPolicy,
    VirtualClock,
)
from robot_registry import create_app

SEEDED_ROBOT = {"id": 1, "sku": "NWR-ARM-6", "name": "A6 Manipulator Arm", "price_cents": 129900}


def make_rig(
    script: FaultScript, policy: RetryPolicy | None = None
) -> tuple[httpx.AsyncClient, VirtualClock, FaultInjectionMiddleware]:
    clock = VirtualClock()
    app = create_app()
    app.state.db[1] = dict(SEEDED_ROBOT)
    middleware = FaultInjectionMiddleware(app, script, clock.sleep)
    inner = httpx.ASGITransport(app=middleware)
    transport = ResilientTransport(inner, policy or RetryPolicy(), clock.sleep)
    client = httpx.AsyncClient(transport=transport, base_url="http://faults.test")
    return client, clock, middleware


def run(coro):  # keep pytest asyncio-plugin free
    return asyncio.run(coro)


def test_recovers_from_transient_errors() -> None:
    async def scenario() -> tuple[int, list[float]]:
        client, clock, _ = make_rig(FaultScript([Fault(FaultKind.ERROR), Fault(FaultKind.ERROR), None]))
        async with client:
            resp = await client.get("/robots/1")
        return resp.status_code, clock.sleeps

    status, sleeps = run(scenario())
    assert status == 200
    assert sleeps == [0.1, 0.2]  # exponential backoff on the virtual clock


def test_latency_fault_is_injected_on_virtual_time_only() -> None:
    async def scenario() -> tuple[int, float]:
        client, clock, _ = make_rig(
            FaultScript([Fault(FaultKind.LATENCY, delay_ms=250)]),
            RetryPolicy(retries=0),
        )
        async with client:
            resp = await client.get("/robots/1")
        return resp.status_code, clock.now

    status, virtual_now = run(scenario())
    assert status == 200
    assert virtual_now == 0.25  # recorded, not slept


def test_abort_retries_then_surfaces_transport_error() -> None:
    async def scenario() -> list[float]:
        client, clock, _ = make_rig(
            FaultScript([Fault(FaultKind.ABORT), Fault(FaultKind.ABORT)]),
            RetryPolicy(retries=1),
        )
        async with client:
            with pytest.raises(ConnectionResetError):
                await client.get("/robots/1")
        return clock.sleeps

    assert run(scenario()) == [0.1]


def test_circuit_breaker_fails_fast_after_threshold() -> None:
    async def scenario() -> tuple[int, int]:
        client, _, middleware = make_rig(
            FaultScript([Fault(FaultKind.ERROR)] * 5),
            RetryPolicy(retries=0, breaker_threshold=2),
        )
        async with client:
            first = await client.get("/robots/1")   # 503 -> failures = 1
            second = await client.get("/robots/1")  # 503 -> failures = 2 (threshold)
            assert (first.status_code, second.status_code) == (503, 503)
            with pytest.raises(BreakerOpenError):
                await client.get("/robots/1")       # short-circuited
        return middleware.requests_seen, client is not None and 1

    requests_seen, _ = run(scenario())
    assert requests_seen == 2  # third call never reached the middleware


def test_healthy_passthrough_needs_no_retries() -> None:
    async def scenario() -> tuple[int, list[float], int]:
        client, clock, middleware = make_rig(FaultScript([]))
        async with client:
            resp = await client.get("/robots/1")
        return resp.status_code, clock.sleeps, middleware.requests_seen

    status, sleeps, seen = run(scenario())
    assert (status, sleeps, seen) == (200, [], 1)
