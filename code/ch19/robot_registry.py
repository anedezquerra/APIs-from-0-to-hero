"""Northwind Robotics robot registry: the single API under test in Chapter 19.

``create_app`` ships with two deliberate-defect knobs so the lab can *break*
the API on demand:

* ``breaking=True`` renames the ``sku`` field to ``part_number`` in every
  response body -- the classic contract-breaking change a provider team
  ships believing it is "internal".
* ``bug_at_price=N`` makes ``POST /robots`` return an unhandled 500 (not
  RFC 9457 shaped) whenever ``price_cents == N`` -- a planted bug for the
  fuzzer to find and shrink.

Offline-first: every consumer of this module talks to the app in-process
through ``httpx.ASGITransport``; no socket is ever opened.
"""
from __future__ import annotations

import asyncio
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

PROBLEM_BASE = "https://northwind-robotics.example/problems"


class SyncASGITransport(httpx.BaseTransport):
    """Sync shim over ``httpx.ASGITransport`` (async-only since httpx 0.28).

    Runs the ASGI app on one dedicated event loop, in-process: no sockets,
    no network, fully offline.
    """

    def __init__(self, app: Any) -> None:
        self._inner = httpx.ASGITransport(app=app)
        self._loop = asyncio.new_event_loop()

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        async_resp = self._loop.run_until_complete(
            self._inner.handle_async_request(request)
        )
        content = self._loop.run_until_complete(async_resp.aread())
        # Rebuild with a byte body so the sync client gets a SyncByteStream.
        return httpx.Response(
            status_code=async_resp.status_code,
            headers=async_resp.headers,
            content=content,
        )


def make_sync_client(app: Any, base_url: str = "http://testserver") -> httpx.Client:
    """Build a synchronous httpx client wired straight into the ASGI app."""
    return httpx.Client(transport=SyncASGITransport(app), base_url=base_url)


class RobotCreate(BaseModel):
    """Payload accepted by ``POST /robots``."""

    sku: str = Field(min_length=3, max_length=32)
    name: str = Field(min_length=1, max_length=80)
    price_cents: int = Field(ge=0, le=10_000_000)


class Robot(RobotCreate):
    """Stored representation: everything in ``RobotCreate`` plus a server id."""

    id: int


def _problem(status: int, title: str, detail: str, instance: str) -> JSONResponse:
    """Build an RFC 9457 problem-details response."""
    slug = title.lower().replace(" ", "-")
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": f"{PROBLEM_BASE}/{slug}",
            "title": title,
            "status": status,
            "detail": detail,
            "instance": instance,
        },
    )


def create_app(*, breaking: bool = False, bug_at_price: int | None = None) -> FastAPI:
    """Application factory; defect knobs are keyword-only and default to off."""
    app = FastAPI(title="Northwind Robotics -- Robot Registry")
    app.state.db = {}  # type: dict[int, dict[str, Any]]
    app.state.next_id = 1

    @app.exception_handler(RequestValidationError)
    async def on_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        first = errors[0] if errors else {}
        loc = ".".join(str(part) for part in first.get("loc", []))
        detail = f"{loc}: {first.get('msg', 'invalid request')}"
        return _problem(422, "Validation Error", detail, request.url.path)

    @app.exception_handler(HTTPException)
    async def on_http_error(request: Request, exc: HTTPException) -> JSONResponse:
        title = "Not Found" if exc.status_code == 404 else "HTTP Error"
        return _problem(exc.status_code, title, str(exc.detail), request.url.path)

    def present(record: dict[str, Any]) -> dict[str, Any]:
        """Serialize a stored record, applying the deliberate break if asked."""
        body = dict(record)
        if breaking:
            body["part_number"] = body.pop("sku")
        return body

    @app.post("/robots", status_code=201)
    async def create_robot(payload: RobotCreate) -> Any:
        if bug_at_price is not None and payload.price_cents == bug_at_price:
            # Planted bug: an unstructured, non-RFC-9457 server error.
            return JSONResponse(status_code=500, content={"oops": "price demon"})
        robot_id = app.state.next_id
        app.state.next_id += 1
        record = {"id": robot_id, **payload.model_dump()}
        app.state.db[robot_id] = record
        return present(record)

    @app.get("/robots/{robot_id}")
    async def get_robot(robot_id: int) -> dict[str, Any]:
        if robot_id not in app.state.db:
            raise HTTPException(status_code=404, detail=f"robot {robot_id} not found")
        return present(app.state.db[robot_id])

    return app
