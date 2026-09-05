"""Northwind Robotics API Platform -- integrative slice (Chapter 21).

One FastAPI application assembling the book's core patterns into a
single deployable unit:

* REST catalog with keyset pagination          (Ch. 6, Ch. 8)
* GraphQL read model over the same domain data (Ch. 12)
* SSE telemetry stream                         (Ch. 11)
* RFC 9457 problem-details errors              (Ch. 7)
* Idempotency keys on order creation           (Ch. 10)
* IETF rate-limit response headers             (Ch. 14)

Offline, deterministic, synthetic data only. Python 3.11+.
"""

from __future__ import annotations

import base64
import threading
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

import strawberry
import uvicorn
from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from strawberry.fastapi import GraphQLRouter

# --- Domain data (synthetic Northwind Robotics universe) -------------------

PRODUCTS: list[dict[str, object]] = [
    {
        "id": 1,
        "sku": "NWR-ARM-6X",
        "name": "Northwind 6-Axis Arm",
        "category": "manipulators",
        "unit_price_cents": 12_500_00,
    },
    {
        "id": 2,
        "sku": "NWR-LDR-360",
        "name": "LiDAR 360 Scanner",
        "category": "sensors",
        "unit_price_cents": 3_499_00,
    },
    {
        "id": 3,
        "sku": "NWR-DRV-BLDC",
        "name": "BLDC Motor Driver",
        "category": "actuators",
        "unit_price_cents": 189_99,
    },
]

AVAILABILITY: dict[str, int] = {
    "NWR-ARM-6X": 4,
    "NWR-LDR-360": 12,
    "NWR-DRV-BLDC": 61,
}

ROBOT_TELEMETRY: dict[str, dict[str, float | int]] = {
    "R-101": {"motor_temp_c": 41.2, "cycles": 18233},
    "R-102": {"motor_temp_c": 38.7, "cycles": 12004},
    "R-103": {"motor_temp_c": 44.9, "cycles": 25077},
}

DEMO_API_KEY = "dev-key-northwind"
RATE_LIMIT = 30
API_VERSION = "2026-09-01"


# --- Errors: RFC 9457 problem details (Ch. 7) ------------------------------

def problem(status: int, title: str, detail: str, type_: str = "about:blank") -> JSONResponse:
    """Build an RFC 9457 ``application/problem+json`` response."""
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={"type": type_, "title": title, "status": status, "detail": detail},
    )


# --- Platform state: rate limiting (Ch. 14) and idempotency (Ch. 10) -------

@dataclass
class PlatformState:
    """Mutable application state guarded by one lock (demo-scale)."""

    lock: threading.Lock = field(default_factory=threading.Lock)
    remaining: int = RATE_LIMIT
    orders: dict[str, dict[str, object]] = field(default_factory=dict)
    next_order_id: int = 1


class CursorError(ValueError):
    """Raised when a keyset pagination cursor cannot be decoded."""


# --- Schemas ----------------------------------------------------------------

class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    category: str
    unit_price_cents: int


class ProductPage(BaseModel):
    items: list[ProductOut]
    next_cursor: str | None = None
    api_version: str


class OrderIn(BaseModel):
    sku: str
    quantity: int = Field(ge=1, le=100)


class OrderOut(BaseModel):
    order_id: str
    sku: str
    quantity: int
    status: str
    api_version: str


def _encode_cursor(product_id: int) -> str:
    return base64.urlsafe_b64encode(f"cursor:{product_id}".encode()).decode()


def _decode_cursor(cursor: str) -> int:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    prefix, _, value = raw.partition(":")
    if prefix != "cursor" or not value.isdigit():
        raise ValueError(f"malformed cursor: {cursor!r}")
    return int(value)


# --- GraphQL read model (Ch. 12) -------------------------------------------

@strawberry.type
class CatalogItem:
    sku: str
    name: str
    category: str
    unit_price_cents: int
    availability: int


@strawberry.type
class RobotStatus:
    robot_id: str
    motor_temp_c: float
    cycles: int


@strawberry.type
class GraphQuery:
    @strawberry.field
    def catalog(self, category: str | None = None) -> list[CatalogItem]:
        rows = PRODUCTS
        if category is not None:
            rows = [p for p in rows if p["category"] == category]
        return [
            CatalogItem(
                sku=str(p["sku"]),
                name=str(p["name"]),
                category=str(p["category"]),
                unit_price_cents=int(p["unit_price_cents"]),
                availability=AVAILABILITY.get(str(p["sku"]), 0),
            )
            for p in rows
        ]

    @strawberry.field
    def robot_status(self, robot_id: str) -> RobotStatus | None:
        row = ROBOT_TELEMETRY.get(robot_id)
        if row is None:
            return None
        return RobotStatus(
            robot_id=robot_id,
            motor_temp_c=float(row["motor_temp_c"]),
            cycles=int(row["cycles"]),
        )


graphql_router = GraphQLRouter(strawberry.Schema(query=GraphQuery))


# --- Application factory -----------------------------------------------------

def create_app(state: PlatformState | None = None) -> FastAPI:
    """Build the platform app; inject state to keep tests isolated."""
    app = FastAPI(title="Northwind Robotics API Platform", version="1.0.0")
    platform = state or PlatformState()

    @app.middleware("http")
    async def platform_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        if request.url.path in ("/healthz", "/docs", "/openapi.json"):
            return await call_next(request)
        if request.headers.get("X-API-Key") != DEMO_API_KEY:
            return problem(401, "Unauthorized", "missing or invalid X-API-Key header")
        with platform.lock:
            if platform.remaining <= 0:
                return JSONResponse(
                    status_code=429,
                    media_type="application/problem+json",
                    headers={"Retry-After": "30", "RateLimit": f'"limit={RATE_LIMIT}"'},
                    content={
                        "type": "about:blank",
                        "title": "Too Many Requests",
                        "status": 429,
                        "detail": "quota exhausted; retry after the Retry-After window",
                    },
                )
            platform.remaining -= 1
            remaining = platform.remaining
        response = await call_next(request)
        response.headers["RateLimit"] = f'"limit={RATE_LIMIT}, remaining={remaining}"'
        response.headers["RateLimit-Remaining"] = str(remaining)
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        detail = "; ".join(
            f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in exc.errors()
        )
        return problem(422, "Unprocessable Entity", detail)

    # --- REST catalog (Ch. 6 + Ch. 8) -------------------------------------
    @app.get("/v1/products", response_model=ProductPage)
    def list_products(
        category: str | None = None,
        limit: int = Query(default=2, ge=1, le=50),
        cursor: str | None = None,
    ) -> ProductPage:
        rows = [p for p in PRODUCTS if category is None or p["category"] == category]
        rows.sort(key=lambda p: int(p["id"]))
        if cursor is not None:
            try:
                after = _decode_cursor(cursor)
            except ValueError as exc:
                raise CursorError(str(exc)) from exc
            rows = [p for p in rows if int(p["id"]) > after]
        page = rows[:limit]
        next_cursor = (
            _encode_cursor(int(page[-1]["id"])) if len(rows) > limit else None
        )
        return ProductPage(
            items=[ProductOut(**p) for p in page],  # type: ignore[arg-type]
            next_cursor=next_cursor,
            api_version=API_VERSION,
        )

    @app.exception_handler(CursorError)
    async def cursor_handler(_request: Request, exc: CursorError) -> JSONResponse:
        return problem(400, "Invalid Cursor", str(exc))

    # --- Orders with idempotency keys (Ch. 10) -----------------------------
    @app.post("/v1/orders", response_model=OrderOut, status_code=201)
    def create_order(order: OrderIn, request: Request) -> OrderOut | JSONResponse:
        key = request.headers.get("Idempotency-Key")
        if not key:
            return problem(
                400,
                "Missing Idempotency-Key",
                "POST /v1/orders requires an Idempotency-Key header",
            )
        with platform.lock:
            existing = platform.orders.get(key)
            if existing is not None:
                if existing["payload"] != order.model_dump():
                    return problem(
                        422,
                        "Idempotency Conflict",
                        "key reused with a different request payload",
                    )
                return OrderOut(
                    order_id=str(existing["order_id"]),
                    sku=order.sku,
                    quantity=order.quantity,
                    status="accepted",
                    api_version=API_VERSION,
                )
            if order.sku not in AVAILABILITY:
                return problem(404, "Unknown SKU", f"no catalog entry for {order.sku!r}")
            order_id = f"ORD-{platform.next_order_id:04d}"
            platform.next_order_id += 1
            platform.orders[key] = {
                "order_id": order_id,
                "payload": order.model_dump(),
            }
        return OrderOut(
            order_id=order_id,
            sku=order.sku,
            quantity=order.quantity,
            status="accepted",
            api_version=API_VERSION,
        )

    # --- SSE telemetry stream (Ch. 11) --------------------------------------
    @app.get("/v1/telemetry/stream")
    async def telemetry_stream() -> StreamingResponse:
        async def events() -> AsyncIterator[str]:
            event_id = 0
            for robot_id in sorted(ROBOT_TELEMETRY):
                row = ROBOT_TELEMETRY[robot_id]
                event_id += 1
                yield (
                    f"id: {event_id}\n"
                    f"event: robot-reading\n"
                    f'data: {{"robot_id": "{robot_id}", '
                    f'"motor_temp_c": {row["motor_temp_c"]}, '
                    f'"cycles": {row["cycles"]}}}\n\n'
                )

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(graphql_router, prefix="/graphql")
    return app


if __name__ == "__main__":
    uvicorn.run(create_app(), host="127.0.0.1", port=8121)
