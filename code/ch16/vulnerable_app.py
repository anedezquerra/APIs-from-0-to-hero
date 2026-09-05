"""================================================================
INTENTIONALLY INSECURE TEACHING MATERIAL -- DO NOT DEPLOY. DO NOT IMITATE.
================================================================
Northwind Robotics fleet API, seeded with all ten OWASP API Security Top 10
(2023) flaws. Every flaw is fenced with a comment naming its OWASP item.
The hardened counterpart is hardened_app.py; the exploit suite is
test_exploit_suite.py. All network I/O goes through fake_network.py, so the
whole file runs offline.
"""

from __future__ import annotations

import base64
import traceback
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fake_network import make_client

# A synthetic "master key" used by the broken authenticator below.
# OWASP API2 (hardcoded credential). Clearly fake; never a real secret.
MASTER_KEY = "sk_test_DEMO_masterkey_invalid"

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

PROMO_BALANCE = {"NWR-LAUNCH": 100}  # code -> remaining units


# ----------------------------------------
# OWASP API2:2023 -- Broken Authentication
# "Tokens" are unsigned base64 of "user:<name>"; anyone can mint one for any
# user. A hardcoded master key bypasses everything. No expiry, no signature.
# ----------------------------------------
def vulnerable_auth(request: Request) -> dict[str, Any]:
    header = request.headers.get("authorization", "")
    token = header.removeprefix("Bearer ").strip()
    if token == MASTER_KEY:  # hardcoded backdoor credential
        return {"username": "master", "role": "admin", "tenant": "tenant-nwr"}
    try:
        decoded = base64.b64decode(token).decode()
        username = decoded.split(":", 1)[1]
        return USERS[username]
    except Exception:
        # Fail-open flavoured: anonymous requests still get a context object,
        # and several endpoints below forget to check it at all.
        return {"username": "anonymous", "role": "none", "tenant": "tenant-nwr"}


def forge_token(username: str) -> str:
    """Helper used by the exploit suite: mint a 'valid' token for anyone."""
    return base64.b64encode(f"user:{username}".encode()).decode()


def create_app() -> FastAPI:
    app = FastAPI(title="NWR Fleet API (VULNERABLE TEACHING BUILD)")

    # ----------------------------------------
    # OWASP API8:2023 -- Security Misconfiguration
    # Wildcard CORS with credentials; stack traces returned to clients;
    # a debug endpoint that dumps configuration including secrets.
    # ----------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def verbose_errors(request: Request, exc: Exception) -> JSONResponse:
        # Leaks internals (paths, library versions) to any caller.
        return JSONResponse(
            status_code=500,
            content={"error": str(exc), "trace": traceback.format_exc()},
        )

    @app.get("/v1/debug/config")
    def debug_config() -> dict[str, Any]:
        return {
            "env": "prod",
            "master_key": MASTER_KEY,
            "db_dsn": "postgres://svc:FAKE_PASS_invalid@db.internal:5432/fleet",
            "flags": {"debug": True, "stack_traces": True},
        }

    # ----------------------------------------
    # OWASP API1:2023 -- Broken Object Level Authorization
    # OWASP API3:2023 -- Excessive Data Exposure (service_key, owner fields,
    # tenant internals all serialized straight back).
    # Sequential integer ids make enumeration trivial: 1001, 1002, ...
    # ----------------------------------------
    @app.get("/v1/robots/{robot_id}")
    def get_robot(
        robot_id: int, user: dict[str, Any] = Depends(vulnerable_auth)
    ) -> dict[str, Any]:
        # user is fetched but never checked against the object. Anyone
        # authenticated (or 'anonymous') reads anyone's robot, secrets included.
        return dict(ROBOTS[robot_id])

    # ----------------------------------------
    # OWASP API3:2023 -- Broken Object Property Level Authorization
    # (mass assignment): the request body is merged wholesale into the record,
    # so clients can set owner_id, service_key, maintenance_mode, anything.
    # ----------------------------------------
    @app.patch("/v1/robots/{robot_id}")
    def patch_robot(
        robot_id: int,
        patch: dict[str, Any],
        user: dict[str, Any] = Depends(vulnerable_auth),
    ) -> dict[str, Any]:
        record = ROBOTS[robot_id]
        record.update(patch)  # <-- the entire flaw in one line
        return dict(record)

    # ----------------------------------------
    # OWASP API4:2023 -- Unrestricted Resource Consumption
    # No pagination ceiling; unbounded simulation parameter; no body limits.
    # ----------------------------------------
    @app.get("/v1/robots")
    def list_robots(limit: int = 10) -> list[dict[str, Any]]:
        # limit=1000000 is accepted happily; there is no cap.
        return [dict(r) for r in list(ROBOTS.values())[:limit]]

    @app.post("/v1/fleet/simulate")
    def simulate(steps: int = 100) -> dict[str, Any]:
        # The 2025 incident ran steps=40_000_000 per request until the pool
        # starved. Loop truncated in the lab so the test suite stays fast;
        # the flaw is that `steps` is accepted and trusted at all.
        work = 0
        for _ in range(min(steps, 20_000)):
            work += 1
        return {"requested_steps": steps, "executed_steps": work}

    # ----------------------------------------
    # OWASP API5:2023 -- Broken Function Level Authorization
    # The admin surface checks authentication, never the role.
    # ----------------------------------------
    @app.get("/v1/admin/users")
    def admin_users(user: dict[str, Any] = Depends(vulnerable_auth)) -> Any:
        return list(USERS.values())  # any authenticated (or anon) caller

    # ----------------------------------------
    # OWASP API6:2023 -- Unrestricted Access to Sensitive Business Flows
    # Promo redemption has no rate limit, no CAPTCHA, no velocity checks:
    # a script drains the campaign budget in seconds.
    # ----------------------------------------
    @app.post("/v1/promo/redeem")
    def redeem_promo(
        body: dict[str, Any], user: dict[str, Any] = Depends(vulnerable_auth)
    ) -> dict[str, Any]:
        code = str(body.get("code", ""))
        if PROMO_BALANCE.get(code, 0) <= 0:
            return JSONResponse(status_code=409, content={"error": "exhausted"})  # type: ignore[return-value]
        PROMO_BALANCE[code] -= 1
        return {"redeemed": code, "remaining": PROMO_BALANCE[code]}

    # ----------------------------------------
    # OWASP API7:2023 -- Server-Side Request Forgery
    # The "diagnostics" feature fetches any caller-supplied URL server-side:
    # internal hosts, the cloud metadata endpoint, anything.
    # ----------------------------------------
    @app.post("/v1/diagnostics/fetch")
    def diagnostics_fetch(
        body: dict[str, Any], user: dict[str, Any] = Depends(vulnerable_auth)
    ) -> dict[str, Any]:
        url = str(body.get("url", ""))
        with make_client() as client:  # simulated network; real one in prod
            response = client.get(url, follow_redirects=True)
        return {"url": url, "status": response.status_code, "body": response.text}

    # ----------------------------------------
    # OWASP API9:2023 -- Improper Inventory Management
    # Legacy v0, shipped "temporarily" in 2023, still live, no auth at all.
    # An internal export route that never made it into the OpenAPI spec.
    # ----------------------------------------
    @app.get("/v0/robots")
    def legacy_robots() -> list[dict[str, Any]]:
        return [dict(r) for r in ROBOTS.values()]  # unauthenticated

    @app.get("/internal/export")
    def internal_export() -> dict[str, Any]:
        return {"users": list(USERS.values()), "robots": list(ROBOTS.values())}

    # ----------------------------------------
    # OWASP API10:2023 -- Unsafe Consumption of APIs
    # The enrichment job trusts the upstream partner completely: every field
    # it returns is merged into our record -- including maintenance_mode.
    # ----------------------------------------
    @app.post("/v1/fleet/enrich/{robot_id}")
    def enrich_robot(
        robot_id: int, user: dict[str, Any] = Depends(vulnerable_auth)
    ) -> dict[str, Any]:
        with make_client() as client:
            upstream = client.get("http://untrusted.maps.example/site")
        payload = upstream.json()  # no schema, no validation, total trust
        ROBOTS[robot_id].update(payload)
        return dict(ROBOTS[robot_id])

    return app


app = create_app()
