"""Property-based tests for the robot registry, plus a stateful rule suite.

Invariants under test:

* ``POST /robots`` never returns 5xx, whatever the payload.
* A 201 response always validates against the published response schema.
* A 4xx response is always RFC 9457 problem-shaped.
* ``GET /robots/{id}`` never returns 5xx for arbitrary integer ids.
* Rule-based sequences (create -> read) stay consistent with a local model.

Deterministic: ``derandomize=True`` replays the same examples every run and
no Hypothesis example database is consulted.

Run:  pytest test_pbt_robots.py -q
"""
from __future__ import annotations

from typing import Any

import jsonschema
from hypothesis import given, settings, strategies as st
from hypothesis.stateful import (
    Bundle,
    RuleBasedStateMachine,
    invariant,
    rule,
)

from robot_registry import create_app, make_sync_client

CLIENT = make_sync_client(create_app(), base_url="http://pbt.test")

ROBOT_SCHEMA: dict[str, Any] = {
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

# Deliberately hostile: wrong types, None, out-of-range ints, over/under strings.
HOSTILE_PAYLOADS = st.fixed_dictionaries(
    {
        "sku": st.one_of(st.text(min_size=0, max_size=40), st.integers(), st.none()),
        "name": st.one_of(st.text(max_size=100), st.booleans(), st.none()),
        "price_cents": st.one_of(
            st.integers(min_value=-1_000_000, max_value=20_000_000),
            st.text(max_size=10),
            st.none(),
        ),
    }
)

VALID_PAYLOADS = st.fixed_dictionaries(
    {
        "sku": st.text(
            alphabet=st.characters(categories=("Lu", "Ll", "Nd"), include_characters="-"),
            min_size=3,
            max_size=32,
        ),
        "name": st.text(
            alphabet=st.characters(categories=("Lu", "Ll", "Nd", "Zs"), include_characters="-"),
            min_size=1,
            max_size=80,
        ),
        "price_cents": st.integers(min_value=0, max_value=10_000_000),
    }
)

DETERMINISTIC = dict(derandomize=True, database=None, deadline=None)


def assert_problem_shape(body: Any, status: int) -> None:
    assert isinstance(body, dict), f"4xx body must be a JSON object, got {body!r}"
    missing = PROBLEM_MEMBERS - body.keys()
    assert not missing, f"problem details missing members: {missing}"
    assert body["status"] == status


@given(payload=HOSTILE_PAYLOADS)
@settings(max_examples=60, **DETERMINISTIC)
def test_create_robot_never_5xx_and_always_schema_conformant(payload: dict) -> None:
    resp = CLIENT.post("/robots", json=payload)
    assert resp.status_code < 500, f"5xx for payload {payload!r}: {resp.text}"
    if resp.status_code == 201:
        jsonschema.validate(resp.json(), ROBOT_SCHEMA)
    else:
        assert resp.status_code == 422, f"unexpected status {resp.status_code}"
        assert resp.headers["content-type"].startswith("application/problem+json")
        assert_problem_shape(resp.json(), 422)


@given(robot_id=st.integers(min_value=-1_000, max_value=1_000))
@settings(max_examples=50, **DETERMINISTIC)
def test_get_robot_never_5xx(robot_id: int) -> None:
    resp = CLIENT.get(f"/robots/{robot_id}")
    assert resp.status_code in (200, 404), f"unexpected status {resp.status_code}"
    if resp.status_code == 200:
        jsonschema.validate(resp.json(), ROBOT_SCHEMA)
    else:
        assert_problem_shape(resp.json(), 404)


class RobotRegistryMachine(RuleBasedStateMachine):
    """Rule-based stateful test: random create/read sequences checked against
    a local model of the registry."""

    created_ids: Bundle[int] = Bundle("created_ids")

    def __init__(self) -> None:
        super().__init__()
        self.client = make_sync_client(create_app(), base_url="http://pbt-stateful.test")
        self.model: dict[int, dict[str, Any]] = {}

    @rule(target=created_ids, payload=VALID_PAYLOADS)
    def create_robot(self, payload: dict[str, Any]) -> int:
        resp = self.client.post("/robots", json=payload)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        jsonschema.validate(body, ROBOT_SCHEMA)
        self.model[body["id"]] = body
        return body["id"]

    @rule(robot_id=created_ids)
    def read_back_matches_model(self, robot_id: int) -> None:
        resp = self.client.get(f"/robots/{robot_id}")
        assert resp.status_code == 200
        assert resp.json() == self.model[robot_id]

    @invariant()
    def every_created_robot_is_readable(self) -> None:
        for robot_id in self.model:
            resp = self.client.get(f"/robots/{robot_id}")
            assert resp.status_code == 200, f"robot {robot_id} vanished"


RobotRegistryMachine.TestCase.settings = settings(
    max_examples=15, stateful_step_count=20, **DETERMINISTIC
)
TestRobotRegistry = RobotRegistryMachine.TestCase
