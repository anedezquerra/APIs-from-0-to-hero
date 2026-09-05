"""In-process smoke tests for the Northwind platform slice.

Every request runs through httpx + ASGITransport: no sockets, no
network, fully deterministic. The suite proves the four surfaces
(REST, GraphQL, SSE, problem-details errors) work together on one app.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from northwind_platform import DEMO_API_KEY, create_app

AUTH = {"X-API-Key": DEMO_API_KEY}


@pytest.fixture()
def client() -> Iterator[TestClient]:
    """Fresh app + in-process client per test (isolated rate limiter)."""
    with TestClient(create_app()) as c:
        yield c


# --- Auth and rate limiting --------------------------------------------------

def test_missing_api_key_is_problem_json(client: TestClient) -> None:
    r = client.get("/v1/products")
    assert r.status_code == 401
    assert r.headers["content-type"] == "application/problem+json"
    body = r.json()
    assert body["status"] == 401
    assert {"type", "title", "status", "detail"} <= body.keys()


def test_rate_limit_headers_present(client: TestClient) -> None:
    r = client.get("/v1/products", headers=AUTH)
    assert r.status_code == 200
    assert "RateLimit" in r.headers
    assert int(r.headers["RateLimit-Remaining"]) < 30


def test_rate_limit_exhaustion_returns_429() -> None:
    with TestClient(create_app()) as c:
        last = None
        for _ in range(31):
            last = c.get("/v1/products", headers=AUTH)
        assert last is not None and last.status_code == 429
        assert last.headers["Retry-After"] == "30"


# --- REST catalog ------------------------------------------------------------

def test_product_page_one_and_cursor(client: TestClient) -> None:
    page1 = client.get("/v1/products", headers=AUTH, params={"limit": 2}).json()
    assert len(page1["items"]) == 2
    assert page1["next_cursor"] is not None
    assert page1["api_version"]

    page2 = client.get(
        "/v1/products",
        headers=AUTH,
        params={"limit": 2, "cursor": page1["next_cursor"]},
    ).json()
    assert len(page2["items"]) == 1
    assert page2["next_cursor"] is None
    ids = [p["id"] for p in page1["items"] + page2["items"]]
    assert ids == [1, 2, 3]


def test_bad_cursor_is_problem_400(client: TestClient) -> None:
    r = client.get(
        "/v1/products", headers=AUTH, params={"cursor": "not-a-cursor"}
    )
    assert r.status_code == 400
    assert r.json()["title"] == "Invalid Cursor"


def test_validation_error_is_problem_422(client: TestClient) -> None:
    r = client.get("/v1/products", headers=AUTH, params={"limit": 0})
    assert r.status_code == 422
    assert r.headers["content-type"] == "application/problem+json"


# --- Orders + idempotency -----------------------------------------------------

def test_order_requires_idempotency_key(client: TestClient) -> None:
    r = client.post("/v1/orders", headers=AUTH, json={"sku": "NWR-ARM-6X", "quantity": 1})
    assert r.status_code == 400


def test_order_replay_returns_same_order_id(client: TestClient) -> None:
    headers = {**AUTH, "Idempotency-Key": "smoke-key-1"}
    payload = {"sku": "NWR-LDR-360", "quantity": 2}
    first = client.post("/v1/orders", headers=headers, json=payload)
    second = client.post("/v1/orders", headers=headers, json=payload)
    assert first.status_code == 201
    assert second.json()["order_id"] == first.json()["order_id"]


def test_idempotency_key_conflict_is_422(client: TestClient) -> None:
    headers = {**AUTH, "Idempotency-Key": "smoke-key-2"}
    client.post("/v1/orders", headers=headers, json={"sku": "NWR-ARM-6X", "quantity": 1})
    conflict = client.post(
        "/v1/orders", headers=headers, json={"sku": "NWR-ARM-6X", "quantity": 9}
    )
    assert conflict.status_code == 422
    assert conflict.json()["title"] == "Idempotency Conflict"


def test_unknown_sku_is_problem_404(client: TestClient) -> None:
    headers = {**AUTH, "Idempotency-Key": "smoke-key-3"}
    r = client.post("/v1/orders", headers=headers, json={"sku": "NOPE-1", "quantity": 1})
    assert r.status_code == 404
    assert r.json()["status"] == 404


# --- GraphQL read model --------------------------------------------------------

def test_graphql_catalog_joins_availability(client: TestClient) -> None:
    query = "{ catalog { sku name availability } }"
    r = client.post("/graphql", headers=AUTH, json={"query": query})
    assert r.status_code == 200
    rows = {item["sku"]: item for item in r.json()["data"]["catalog"]}
    assert rows["NWR-LDR-360"]["availability"] == 12


def test_graphql_robot_status(client: TestClient) -> None:
    query = '{ robotStatus(robotId: "R-101") { robotId motorTempC cycles } }'
    r = client.post("/graphql", headers=AUTH, json={"query": query})
    assert r.status_code == 200
    status = r.json()["data"]["robotStatus"]
    assert status["robotId"] == "R-101"
    assert status["motorTempC"] == pytest.approx(41.2)


# --- SSE telemetry --------------------------------------------------------------

def test_sse_stream_yields_three_robot_events(client: TestClient) -> None:
    with client.stream("GET", "/v1/telemetry/stream", headers=AUTH) as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        body = "".join(r.iter_text())
    events = [chunk for chunk in body.strip().split("\n\n") if chunk]
    assert len(events) == 3
    assert all(chunk.startswith("id: ") for chunk in events)
    payload = events[0].split("data: ", 1)[1]
    assert json.loads(payload)["robot_id"] == "R-101"
