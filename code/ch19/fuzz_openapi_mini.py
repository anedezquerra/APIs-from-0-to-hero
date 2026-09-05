"""Stdlib-only OpenAPI-driven fuzzer: Schemathesis in miniature.

Given the request-body schema of ``POST /robots`` (a stand-in for an excerpt
of the published OpenAPI document), generate boundary and malformed
payloads, fire them at the app in-process, and classify every response:

* 2xx  -> must validate against the response schema;
* 4xx  -> must be RFC 9457 problem-shaped;
* 5xx  -> always a failure.

Includes a greedy shrinker: when a failing payload is found, strip it down
to a minimal reproducer so the report is actionable.

Run the demo:  python fuzz_openapi_mini.py
"""
from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from typing import Any, Callable

import httpx
import jsonschema

from robot_registry import create_app, make_sync_client

# Excerpt of the published OpenAPI 3.1 document: POST /robots request body.
REQUEST_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["sku", "name", "price_cents"],
    "properties": {
        "sku": {"type": "string", "minLength": 3, "maxLength": 32},
        "name": {"type": "string", "minLength": 1, "maxLength": 80},
        "price_cents": {"type": "integer", "minimum": 0, "maximum": 10_000_000},
    },
    "additionalProperties": False,
}

RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["id", "sku", "name", "price_cents"],
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "sku": {"type": "string", "minLength": 3, "maxLength": 32},
        "name": {"type": "string", "minLength": 1, "maxLength": 80},
        "price_cents": {"type": "integer", "minimum": 0, "maximum": 10_000_000},
    },
    "additionalProperties": False,
}

PROBLEM_MEMBERS = {"type", "title", "status", "detail", "instance"}
VALID_BASE: dict[str, Any] = {"sku": "NWR-ARM-6", "name": "A6 Manipulator Arm", "price_cents": 129900}


def boundary_candidates(prop_schema: dict[str, Any]) -> list[Any]:
    """Boundary and malformed candidates for one property schema."""
    ptype = prop_schema.get("type")
    if ptype == "string":
        lo = prop_schema.get("minLength", 0)
        hi = prop_schema.get("maxLength", 16)
        candidates = ["A" * lo, "A" * hi, "", None, 123, True]
        if lo > 0:
            candidates.append("A" * (lo - 1))
        candidates.append("A" * (hi + 1))
        candidates.append("Z" * 512)  # pathological length
        return candidates
    if ptype == "integer":
        lo = prop_schema.get("minimum", 0)
        hi = prop_schema.get("maximum", 100)
        return [lo, hi, lo - 1, hi + 1, 0, -1, 666, 2**31, "10", None, True, 1.5]
    return [None]


def fuzz_cases(schema: dict[str, Any]) -> list[tuple[str, Any]]:
    """All (label, payload) cases derived from the request schema."""
    cases: list[tuple[str, Any]] = []
    properties = schema["properties"]
    for name, prop_schema in properties.items():
        for value in boundary_candidates(prop_schema):
            payload = dict(VALID_BASE, **{name: value})
            cases.append((f"{name}={value!r}"[:60], payload))
    for name in schema.get("required", []):
        payload = {k: v for k, v in VALID_BASE.items() if k != name}
        cases.append((f"missing required {name!r}", payload))
    cases.append(("extra property", dict(VALID_BASE, legacy_field="x")))
    cases.append(("empty object", {}))
    cases.append(("body is a list", [1, 2, 3]))
    cases.append(("body is a string", "not-an-object"))
    cases.append(("body is null", None))
    return cases


@dataclass
class FuzzFailure:
    label: str
    payload: Any
    status: int
    reason: str


def classify(label: str, payload: Any, resp: httpx.Response) -> FuzzFailure | None:
    if resp.status_code >= 500:
        return FuzzFailure(label, payload, resp.status_code, "server error (5xx)")
    if resp.status_code >= 400:
        body = resp.json()
        missing = PROBLEM_MEMBERS - set(body)
        if missing or body.get("status") != resp.status_code:
            return FuzzFailure(
                label, payload, resp.status_code, f"4xx not RFC 9457 shaped: {body!r}"
            )
        return None
    try:
        jsonschema.validate(resp.json(), RESPONSE_SCHEMA)
    except jsonschema.ValidationError as exc:
        return FuzzFailure(label, payload, resp.status_code, f"2xx violates schema: {exc.message}")
    return None


def run_fuzz(
    client: httpx.Client, cases: list[tuple[str, Any]]
) -> tuple[int, list[FuzzFailure]]:
    failures: list[FuzzFailure] = []
    for label, payload in cases:
        resp = client.post("/robots", json=payload)
        failure = classify(label, payload, resp)
        if failure is not None:
            failures.append(failure)
    return len(cases), failures


def minimal_values(prop_schema: dict[str, Any]) -> list[Any]:
    """Smallest schema-valid stand-ins for a property (value minimization)."""
    ptype = prop_schema.get("type")
    if ptype == "string":
        return ["A" * prop_schema.get("minLength", 0)]
    if ptype == "integer":
        return [prop_schema.get("minimum", 0)]
    return [None]


def shrink(
    client: httpx.Client,
    payload: dict[str, Any],
    is_failure: Callable[[httpx.Response], bool],
    schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Greedy minimization: drop keys, then minimize values, while the
    failure still reproduces. Dropping a *required* key usually turns a 500
    into a 422, so value minimization is what isolates the trigger field."""
    minimal = copy.deepcopy(payload)
    for key in sorted(minimal):
        candidate = {k: v for k, v in minimal.items() if k != key}
        if is_failure(client.post("/robots", json=candidate)):
            minimal = candidate
    if schema is not None:
        for key, prop_schema in schema.get("properties", {}).items():
            if key not in minimal:
                continue
            for candidate_value in minimal_values(prop_schema):
                trial = dict(minimal, **{key: candidate_value})
                if is_failure(client.post("/robots", json=trial)):
                    minimal = trial
                    break
    return minimal


def demo() -> None:
    cases = fuzz_cases(REQUEST_SCHEMA)
    healthy = make_sync_client(create_app(), base_url="http://fuzz.test")
    total, failures = run_fuzz(healthy, cases)
    print(f"healthy app:    {total} cases, {len(failures)} failures")

    buggy = make_sync_client(create_app(bug_at_price=666), base_url="http://fuzz.test")
    total, failures = run_fuzz(buggy, cases)
    print(f"buggy app:      {total} cases, {len(failures)} failures")
    if failures:
        first = failures[0]
        minimal = shrink(
            buggy, first.payload, lambda r: r.status_code >= 500, REQUEST_SCHEMA
        )
        print(f"first failure:  {first.label} -> {first.status} ({first.reason})")
        print(f"shrunk to:      {json.dumps(minimal, sort_keys=True)}")


if __name__ == "__main__":
    demo()
