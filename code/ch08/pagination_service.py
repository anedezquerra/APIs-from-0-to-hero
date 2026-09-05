"""Chapter 8 reference service: three pagination strategies over one table.

FastAPI application exposing the Northwind Robotics parts catalog with:

* ``GET /parts/offset``  -- classic LIMIT/OFFSET with RFC 8288 Link headers.
* ``GET /parts/keyset``  -- keyset (seek) pagination with transparent params.
* ``GET /parts/cursor``  -- opaque, HMAC-signed, versioned, expiring cursors.

All three order by ``(unit_cost_cents, id)`` which is backed by the
composite index ``idx_parts_cost_id`` created by ``gen_dataset.py``.

Run the self-check (offline, uses FastAPI TestClient):

    python gen_dataset.py --rows 50000 --db parts.db
    python pagination_service.py
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import JSONResponse

DB_PATH = Path(os.environ.get("PARTS_DB", "parts.db"))
# Demo-only key. In production load from a secrets manager, never hardcode.
CURSOR_SECRET = os.environ.get("CURSOR_SECRET", "northwind-robotics-demo-key")
CURSOR_VERSION = 1
CURSOR_TTL_SECONDS = 3600
MAX_LIMIT = 200
DEFAULT_LIMIT = 50

SELECT_COLS = "id, sku, name, category, unit_cost_cents, weight_grams, active"
ORDER_BY = "unit_cost_cents, id"

app = FastAPI(title="Northwind Robotics Parts API", version="1.0.0")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_part(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "sku": row["sku"],
        "name": row["name"],
        "category": row["category"],
        "unit_cost_cents": row["unit_cost_cents"],
        "weight_grams": row["weight_grams"],
        "active": bool(row["active"]),
    }


def clamp_limit(limit: int) -> int:
    if limit < 1:
        return DEFAULT_LIMIT
    return min(limit, MAX_LIMIT)


def link_header(base_url: str, links: dict[str, str]) -> str:
    """Render an RFC 8288 Link header value from rel -> URL mappings."""
    return ", ".join(f'<{base_url}{target}>; rel="{rel}"' for rel, target in links.items())


# --------------------------------------------------------------------------
# Strategy 1: offset pagination
# --------------------------------------------------------------------------
@app.get("/parts/offset")
def list_parts_offset(
    request: Request,
    response: Response,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    include_total: bool = Query(False),
) -> dict[str, Any]:
    limit = clamp_limit(limit)
    conn = get_db()
    try:
        rows = conn.execute(
            f"SELECT {SELECT_COLS} FROM parts "
            f"ORDER BY {ORDER_BY} LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        body: dict[str, Any] = {"items": [row_to_part(r) for r in rows]}
        if include_total:
            # Deliberately opt-in: COUNT(*) is a full index scan at scale.
            total = conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
            body["total_count"] = total

        base = str(request.url.path)
        links: dict[str, str] = {"first": f"{base}?limit={limit}&offset=0"}
        if rows:
            links["next"] = f"{base}?limit={limit}&offset={offset + limit}"
        if offset > 0:
            prev_offset = max(0, offset - limit)
            links["prev"] = f"{base}?limit={limit}&offset={prev_offset}"
        if "total_count" in body:
            last_offset = max(0, ((body["total_count"] - 1) // limit) * limit)
            links["last"] = f"{base}?limit={limit}&offset={last_offset}"
        response.headers["Link"] = link_header(base, links)
        return body
    finally:
        conn.close()


# --------------------------------------------------------------------------
# Strategy 2: keyset (seek) pagination -- transparent parameters
# --------------------------------------------------------------------------
@app.get("/parts/keyset")
def list_parts_keyset(
    request: Request,
    response: Response,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    after_cost: int | None = Query(None, ge=0),
    after_id: int | None = Query(None, ge=1),
) -> dict[str, Any]:
    limit = clamp_limit(limit)
    conn = get_db()
    try:
        if after_cost is None or after_id is None:
            rows = conn.execute(
                f"SELECT {SELECT_COLS} FROM parts ORDER BY {ORDER_BY} LIMIT ?",
                (limit + 1,),  # fetch one extra row to compute has_more
            ).fetchall()
        else:
            # Tuple comparison keeps the predicate sargable on the
            # composite index (unit_cost_cents, id).
            rows = conn.execute(
                f"SELECT {SELECT_COLS} FROM parts "
                f"WHERE (unit_cost_cents, id) > (?, ?) "
                f"ORDER BY {ORDER_BY} LIMIT ?",
                (after_cost, after_id, limit + 1),
            ).fetchall()

        has_more = len(rows) > limit
        page = rows[:limit]
        body: dict[str, Any] = {
            "items": [row_to_part(r) for r in page],
            "has_more": has_more,
        }
        if has_more and page:
            last = page[-1]
            base = str(request.url.path)
            nxt = (
                f"{base}?limit={limit}"
                f"&after_cost={last['unit_cost_cents']}&after_id={last['id']}"
            )
            response.headers["Link"] = link_header(base, {"next": nxt})
        return body
    finally:
        conn.close()


# --------------------------------------------------------------------------
# Strategy 3: opaque signed cursors (HMAC-SHA256, versioned, expiring)
# --------------------------------------------------------------------------
def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def encode_cursor(last_cost: int, last_id: int) -> str:
    payload = {
        "v": CURSOR_VERSION,
        "exp": int(time.time()) + CURSOR_TTL_SECONDS,
        "cost": last_cost,
        "id": last_id,
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    body = _b64url_encode(raw)
    tag = hmac.new(CURSOR_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{tag[:32]}"


class CursorError(ValueError):
    """Raised for any malformed, forged, or expired cursor."""


def decode_cursor(token: str) -> tuple[int, int]:
    try:
        body, tag = token.rsplit(".", 1)
    except ValueError as exc:
        raise CursorError("cursor is malformed") from exc
    expected = hmac.new(
        CURSOR_SECRET.encode(), body.encode(), hashlib.sha256
    ).hexdigest()[:32]
    if not hmac.compare_digest(expected, tag):
        raise CursorError("cursor signature mismatch")
    try:
        payload = json.loads(_b64url_decode(body))
    except (ValueError, UnicodeDecodeError) as exc:
        raise CursorError("cursor payload is not valid JSON") from exc
    if payload.get("v") != CURSOR_VERSION:
        raise CursorError("unsupported cursor version")
    if int(payload.get("exp", 0)) < int(time.time()):
        raise CursorError("cursor has expired")
    return int(payload["cost"]), int(payload["id"])


@app.get("/parts/cursor")
def list_parts_cursor(
    request: Request,
    response: Response,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    cursor: str | None = Query(None),
) -> dict[str, Any]:
    limit = clamp_limit(limit)
    position: tuple[int, int] | None = None
    if cursor is not None:
        try:
            position = decode_cursor(cursor)
        except CursorError as exc:
            return JSONResponse(
                status_code=400,
                content={
                    "type": "about:blank",
                    "title": "Invalid cursor",
                    "status": 400,
                    "detail": str(exc),
                },
            )

    conn = get_db()
    try:
        if position is None:
            rows = conn.execute(
                f"SELECT {SELECT_COLS} FROM parts ORDER BY {ORDER_BY} LIMIT ?",
                (limit + 1,),
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT {SELECT_COLS} FROM parts "
                f"WHERE (unit_cost_cents, id) > (?, ?) "
                f"ORDER BY {ORDER_BY} LIMIT ?",
                (position[0], position[1], limit + 1),
            ).fetchall()
        has_more = len(rows) > limit
        page = rows[:limit]
        body: dict[str, Any] = {
            "items": [row_to_part(r) for r in page],
            "has_more": has_more,
        }
        if has_more and page:
            last = page[-1]
            token = encode_cursor(last["unit_cost_cents"], last["id"])
            body["next_cursor"] = token
            base = str(request.url.path)
            response.headers["Link"] = link_header(
                base, {"next": f"{base}?limit={limit}&cursor={token}"}
            )
        return body
    finally:
        conn.close()


def _self_check() -> None:
    """Offline verification: page through all three strategies and compare."""
    from fastapi.testclient import TestClient

    if not DB_PATH.exists():
        raise SystemExit(f"database {DB_PATH} missing; run gen_dataset.py first")
    client = TestClient(app)

    expected = get_db().execute(
        "SELECT id FROM parts ORDER BY unit_cost_cents, id LIMIT 250"
    ).fetchall()
    expected_ids = [r[0] for r in expected]

    # Offset: walk five pages of 50.
    seen: list[int] = []
    offset = 0
    for _ in range(5):
        res = client.get(f"/parts/offset?limit=50&offset={offset}")
        assert res.status_code == 200, res.text
        assert "next" in res.headers["Link"]
        seen.extend(item["id"] for item in res.json()["items"])
        offset += 50
    assert seen == expected_ids, "offset walk diverged"

    # Keyset: walk with transparent after_* parameters.
    seen = []
    params: dict[str, Any] = {"limit": 50}
    for _ in range(5):
        res = client.get("/parts/keyset", params=params)
        assert res.status_code == 200, res.text
        payload = res.json()
        seen.extend(item["id"] for item in payload["items"])
        last = payload["items"][-1]
        params = {
            "limit": 50,
            "after_cost": last["unit_cost_cents"],
            "after_id": last["id"],
        }
    assert seen == expected_ids, "keyset walk diverged"

    # Cursor: walk with opaque signed tokens; then tamper and expect 400.
    seen = []
    token: str | None = None
    for _ in range(5):
        params = {"limit": 50} if token is None else {"limit": 50, "cursor": token}
        res = client.get("/parts/cursor", params=params)
        assert res.status_code == 200, res.text
        payload = res.json()
        seen.extend(item["id"] for item in payload["items"])
        token = payload["next_cursor"]
    assert seen == expected_ids, "cursor walk diverged"

    forged = token[:-2] + ("00" if not token.endswith("00") else "11")
    res = client.get("/parts/cursor", params={"limit": 50, "cursor": forged})
    assert res.status_code == 400, res.text

    res = client.get("/parts/offset?limit=50&include_total=true")
    assert res.json()["total_count"] > 0
    assert "last" in res.headers["Link"]
    print("self-check OK: offset, keyset, and cursor strategies agree;" 
          " forged cursor rejected with 400")


if __name__ == "__main__":
    _self_check()
