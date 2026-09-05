"""Hardened Northwind Robotics fleet API -- the exploit suite's green target.

Every endpoint is the repaired counterpart of vulnerable_app.py. Fixes are
commented with the OWASP item they close. Runs fully offline: tokens come
from jwks_fixture.py, outbound I/O from fake_network.py.
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from authz import (
    ROBOT_READ_POLICY,
    ROBOT_WRITE_POLICY,
    ForbiddenError,
    Guard,
    apply_patch,
    filter_fields,
)
from fake_network import make_client, simulated_dns
from jwks_fixture import AUDIENCE, ISSUER, JWKS
from ssrf_fetcher import OutboundPolicy, SafeFetcher, SsrfBlockedError
from token_validation import Principal, TokenValidator, build_auth_dependency

# ----------------------------------------
# Data (same fictional universe as the vulnerable build; secrets never leave
# the store layer now).
# ----------------------------------------
USERS: dict[str, dict[str, Any]] = {
    "alice": {"username": "alice", "role": "operator", "tenant": "tenant-nwr"},
    "bob": {"username": "bob", "role": "operator", "tenant": "tenant-nwr"},
    "carol": {"username": "carol", "role": "admin", "tenant": "tenant-nwr"},
}

ROBOTS: dict[int, dict[str, Any]] = {
    1001: {
        "id": 1001, "name": "Welder-7", "model": "NR-220", "status": "idle",
        "battery_pct": 88, "last_seen": "2026-08-30T09:14:00Z",
        "notes": "dock 3", "owner_id": "alice", "tenant_id": "tenant-nwr",
        "firmware_version": "4.2.0", "service_key": "sk_test_DEMO_robot1001_invalid",
        "service_key_last4": "1001", "maintenance_mode": False,
        "telemetry_channel": "stable",
    },
    1002: {
        "id": 1002, "name": "Lifter-2", "model": "NR-410", "status": "active",
        "battery_pct": 61, "last_seen": "2026-08-30T09:15:00Z",
        "notes": "bay 9", "owner_id": "bob", "tenant_id": "tenant-nwr",
        "firmware_version": "4.1.3", "service_key": "sk_test_DEMO_robot1002_invalid",
        "service_key_last4": "1002", "maintenance_mode": False,
        "telemetry_channel": "stable",
    },
}

PROMO_BALANCE = {"NWR-LAUNCH": 100}
PROMO_LIMIT_PER_PRINCIPAL = 3  # lab stand-in for the Chapter 14 token bucket

OUTBOUND_POLICY = OutboundPolicy(
    allowed_hosts=frozenset({"telemetry.partner-nwr.example"})
)


class PatchRobotRequest(BaseModel):
    """API3 fix (write side): the contract is an explicit schema, and the
    authz layer re-checks every field against the caller's role."""

    model_config = {"extra": "forbid"}
    name: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=500)
    status: Literal["idle", "active", "charging"] | None = None


class FetchRequest(BaseModel):
    model_config = {"extra": "forbid"}
    url: str = Field(max_length=2048)


class PromoRequest(BaseModel):
    model_config = {"extra": "forbid"}
    code: str = Field(max_length=32)


class UpstreamSiteInfo(BaseModel):
    """API10 fix: upstream payloads are parsed against a schema with
    extra fields ignored; only vetted fields ever touch our records."""

    model_config = {"extra": "ignore"}
    label: str = Field(max_length=120)
    telemetry_channel: Literal["stable", "beta"] = "stable"


def create_app() -> FastAPI:
    app = FastAPI(title="NWR Fleet API (hardened)")
    validator = TokenValidator(JWKS, issuer=ISSUER, audience=AUDIENCE)
    principal_dep = build_auth_dependency(validator)
    redeem_counters: dict[str, int] = {}

    # API8 fix: exact origins, no credentials; never the wildcard pair.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://portal.northwind-robotics.example"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Any) -> Any:
        # API8 fix: secure defaults on every response; no stack traces.
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'"
        )
        response.headers.setdefault("Cache-Control", "no-store")
        return response

    @app.exception_handler(ForbiddenError)
    async def forbidden(request: Request, exc: ForbiddenError) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": "forbidden"})

    @app.exception_handler(SsrfBlockedError)
    async def ssrf_blocked(request: Request, exc: SsrfBlockedError) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": "destination blocked"})

    @app.exception_handler(Exception)
    async def opaque_errors(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": "internal error"})

    def guard_for(principal: Principal) -> Guard:
        return Guard(
            actor_id=principal.subject,
            tenant_id=principal.tenant,
            roles=principal.roles,
        )

    def view_roles(principal: Principal) -> list[str]:
        # Owners authenticate with a fleet scope and no role claim; they get
        # the owner field policy. Named roles widen the view per policy.
        return sorted(principal.roles) if principal.roles else ["owner"]

    # API1 fix: fetch, then authorize the *object*; API3 fix (read side):
    # serialize through the role's field policy -- never the raw record.
    @app.get("/v1/robots/{robot_id}")
    def get_robot(
        robot_id: int, principal: Principal = Depends(principal_dep)
    ) -> dict[str, Any]:
        principal.require_scope("fleet:read")
        record = ROBOTS.get(robot_id)
        if record is None:
            raise HTTPException(status_code=404, detail="not found")
        guard_for(principal).require_read(record)
        return filter_fields(record, ROBOT_READ_POLICY, view_roles(principal))

    @app.patch("/v1/robots/{robot_id}")
    def patch_robot(
        robot_id: int,
        patch: PatchRobotRequest,
        principal: Principal = Depends(principal_dep),
    ) -> dict[str, Any]:
        principal.require_scope("fleet:write")
        record = ROBOTS.get(robot_id)
        if record is None:
            raise HTTPException(status_code=404, detail="not found")
        guard_for(principal).require_write(record)
        body = patch.model_dump(exclude_none=True)
        updated = apply_patch(record, body, ROBOT_WRITE_POLICY, principal.roles)
        ROBOTS[robot_id] = updated
        return filter_fields(updated, ROBOT_READ_POLICY, view_roles(principal))

    # API4 fix: hard ceilings at the schema layer; anything bigger is a 422
    # before a single byte of work happens.
    @app.get("/v1/robots")
    def list_robots(
        limit: int = Query(default=10, ge=1, le=100),
        principal: Principal = Depends(principal_dep),
    ) -> list[dict[str, Any]]:
        principal.require_scope("fleet:read")
        mine = [
            r for r in ROBOTS.values() if guard_for(principal).can_read(r)
        ]
        return [
            filter_fields(r, ROBOT_READ_POLICY, view_roles(principal))
            for r in mine[:limit]
        ]

    @app.post("/v1/fleet/simulate")
    def simulate(
        steps: int = Query(default=100, ge=1, le=10_000),
        principal: Principal = Depends(principal_dep),
    ) -> dict[str, Any]:
        principal.require_scope("fleet:command")
        work = 0
        for _ in range(steps):
            work += 1
        return {"executed_steps": work, "cap": 10_000}

    # API5 fix: the admin surface requires the admin role AND scope,
    # checked in the dependency layer, not by convention.
    @app.get("/v1/admin/users")
    def admin_users(
        principal: Principal = Depends(principal_dep),
    ) -> list[dict[str, Any]]:
        principal.require_scope("admin:users")
        if "admin" not in principal.roles:
            raise HTTPException(status_code=403, detail="admin role required")
        return [
            {"username": u["username"], "role": u["role"]} for u in USERS.values()
        ]

    # API6 fix: the sensitive flow is velocity-limited per authenticated
    # principal before business logic runs.
    @app.post("/v1/promo/redeem")
    def redeem_promo(
        body: PromoRequest, principal: Principal = Depends(principal_dep)
    ) -> dict[str, Any]:
        principal.require_scope("promo:redeem")
        used = redeem_counters.get(principal.subject, 0)
        if used >= PROMO_LIMIT_PER_PRINCIPAL:
            return JSONResponse(  # type: ignore[return-value]
                status_code=429,
                content={"detail": "rate limit exceeded"},
                headers={"Retry-After": "60"},
            )
        if PROMO_BALANCE.get(body.code, 0) <= 0:
            raise HTTPException(status_code=409, detail="promotion exhausted")
        redeem_counters[principal.subject] = used + 1
        PROMO_BALANCE[body.code] -= 1
        return {"redeemed": body.code, "remaining": PROMO_BALANCE[body.code]}

    # API7 fix: outbound fetches pass the full SSRF gauntlet -- allow-list,
    # scheme/port checks, DNS pinning, redirect re-validation.
    @app.post("/v1/diagnostics/fetch")
    def diagnostics_fetch(
        body: FetchRequest, principal: Principal = Depends(principal_dep)
    ) -> dict[str, Any]:
        principal.require_scope("diagnostics:run")
        with make_client() as client:
            fetcher = SafeFetcher(OUTBOUND_POLICY, client, resolve=simulated_dns)
            text = fetcher.fetch_text(body.url)
        return {"url": body.url, "body": text}

    # API8 fix: no /v1/debug/config exists. API9 fix: /v0 and /internal/*
    # are gone -- every route is in the OpenAPI spec and inventory.

    # API10 fix: upstream data is parsed against UpstreamSiteInfo; only the
    # vetted telemetry_channel field may flow into our records.
    @app.post("/v1/fleet/enrich/{robot_id}")
    def enrich_robot(
        robot_id: int, principal: Principal = Depends(principal_dep)
    ) -> dict[str, Any]:
        principal.require_scope("fleet:write")
        record = ROBOTS.get(robot_id)
        if record is None:
            raise HTTPException(status_code=404, detail="not found")
        guard_for(principal).require_write(record)
        with make_client() as client:
            upstream = client.get("http://untrusted.maps.example/site")
        try:
            info = UpstreamSiteInfo.model_validate(upstream.json())
        except ValueError as exc:
            raise HTTPException(
                status_code=502, detail="upstream payload failed validation"
            ) from exc
        record["telemetry_channel"] = info.telemetry_channel
        return filter_fields(record, ROBOT_READ_POLICY, view_roles(principal))

    return app


app = create_app()
