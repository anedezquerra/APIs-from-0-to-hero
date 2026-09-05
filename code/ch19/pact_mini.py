"""A mini consumer-driven contract-testing framework, Pact-inspired.

The moving parts mirror the real Pact loop:

1. Consumer side: :class:`PactRecorder` wraps an ``httpx.Client``; every
   interaction the consumer relies on is executed, validated on the spot,
   and frozen into a JSON *pact file*.
2. The pact file is the contract artifact. In production it travels through
   a broker; here it is a plain JSON file under ``pacts\\``.
3. Provider side: :class:`ProviderVerifier` replays each interaction against
   a *fresh* provider application, applying the named *provider state*
   first, and checks status + a recursive body subset match.

Everything is offline: provider replay runs through ``httpx.ASGITransport``.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import httpx

from robot_registry import create_app, make_sync_client

StateHandler = Callable[[Any], None]  # receives the provider FastAPI app
AppFactory = Callable[[], Any]


@dataclass
class Interaction:
    """One request/response pair the consumer depends on."""

    description: str
    provider_state: str | None
    method: str
    path: str
    request_body: dict[str, Any] | None
    expected_status: int
    expected_body_subset: dict[str, Any]

    def to_json(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "providerState": self.provider_state,
            "request": {"method": self.method, "path": self.path, "body": self.request_body},
            "response": {
                "status": self.expected_status,
                "bodySubset": self.expected_body_subset,
            },
        }

    @classmethod
    def from_json(cls, raw: dict[str, Any]) -> "Interaction":
        return cls(
            description=raw["description"],
            provider_state=raw.get("providerState"),
            method=raw["request"]["method"],
            path=raw["request"]["path"],
            request_body=raw["request"].get("body"),
            expected_status=raw["response"]["status"],
            expected_body_subset=raw["response"]["bodySubset"],
        )


def subset_mismatches(expected: Any, actual: Any, path: str = "$") -> list[str]:
    """Recursive subset match: every expected leaf must exist and be equal."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: expected object, got {type(actual).__name__}"]
        problems: list[str] = []
        for key, sub in expected.items():
            if key not in actual:
                problems.append(f"{path}.{key}: missing (expected {sub!r})")
            else:
                problems.extend(subset_mismatches(sub, actual[key], f"{path}.{key}"))
        return problems
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            return [f"{path}: expected list of length {len(expected)}"]
        problems = []
        for i, sub in enumerate(expected):
            problems.extend(subset_mismatches(sub, actual[i], f"{path}[{i}]"))
        return problems
    if expected != actual:
        return [f"{path}: expected {expected!r}, got {actual!r}"]
    return []


class PactRecorder:
    """Consumer side: exercise the API and freeze the interactions relied on."""

    def __init__(self, client: httpx.Client, *, consumer: str, provider: str) -> None:
        self._client = client
        self.consumer = consumer
        self.provider = provider
        self.interactions: list[Interaction] = []

    def record(
        self,
        description: str,
        method: str,
        path: str,
        *,
        provider_state: str | None = None,
        json_body: dict[str, Any] | None = None,
        expected_status: int,
        expect_subset: dict[str, Any],
    ) -> httpx.Response:
        """Execute one interaction; fail the consumer test immediately if the
        API already violates the expectation, then freeze it."""
        resp = self._client.request(method, path, json=json_body)
        if resp.status_code != expected_status:
            raise AssertionError(
                f"[{description}] expected {expected_status}, got "
                f"{resp.status_code}: {resp.text}"
            )
        problems = subset_mismatches(expect_subset, resp.json())
        if problems:
            raise AssertionError(f"[{description}] response mismatches: {problems}")
        self.interactions.append(
            Interaction(
                description=description,
                provider_state=provider_state,
                method=method,
                path=path,
                request_body=json_body,
                expected_status=expected_status,
                expected_body_subset=expect_subset,
            )
        )
        return resp

    def write_pact(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        document = {
            "consumer": {"name": self.consumer},
            "provider": {"name": self.provider},
            "interactions": [i.to_json() for i in self.interactions],
        }
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        return path


@dataclass
class VerificationReport:
    """Outcome of replaying every pact interaction against the provider."""

    results: list[tuple[str, bool, list[str]]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(passed for _, passed, _ in self.results)

    def failures(self) -> list[str]:
        return [f"{desc}: {problems}" for desc, passed, problems in self.results if not passed]

    def render(self) -> str:
        lines = []
        for desc, passed, problems in self.results:
            mark = "PASS" if passed else "FAIL"
            lines.append(f"  [{mark}] {desc}")
            for problem in problems:
                lines.append(f"         {problem}")
        return "\n".join(lines)


class ProviderVerifier:
    """Provider side: replay a pact file against a fresh application instance."""

    def __init__(
        self,
        app_factory: AppFactory,
        pact_path: Path,
        states: dict[str, StateHandler],
    ) -> None:
        self._app_factory = app_factory
        self._pact_path = pact_path
        self._states = states

    def verify(self) -> VerificationReport:
        document = json.loads(self._pact_path.read_text(encoding="utf-8"))
        report = VerificationReport()
        for raw in document["interactions"]:
            interaction = Interaction.from_json(raw)
            problems: list[str] = []
            app = self._app_factory()
            if interaction.provider_state is not None:
                handler = self._states.get(interaction.provider_state)
                if handler is None:
                    problems.append(f"unknown provider state: {interaction.provider_state!r}")
                else:
                    handler(app)
            if not problems:
                client = make_sync_client(app, base_url="http://provider.test")
                resp = client.request(
                    interaction.method,
                    interaction.path,
                    json=interaction.request_body,
                )
                if resp.status_code != interaction.expected_status:
                    problems.append(
                        f"status: expected {interaction.expected_status}, "
                        f"got {resp.status_code}"
                    )
                if interaction.expected_body_subset:
                    try:
                        body = resp.json()
                    except json.JSONDecodeError:
                        problems.append("response body is not JSON")
                    else:
                        problems.extend(subset_mismatches(
                            interaction.expected_body_subset, body
                        ))
            report.results.append((interaction.description, not problems, problems))
        return report


# --------------------------------------------------------------------------
# Demo consumer: the Northwind Robotics fulfillment service.
# --------------------------------------------------------------------------

def _seed_robot_7(app: Any) -> None:
    """Provider state: 'a robot with id 7 exists'."""
    app.state.db[7] = {
        "id": 7,
        "sku": "NWR-ARM-6",
        "name": "A6 Manipulator Arm",
        "price_cents": 129900,
    }


PROVIDER_STATES: dict[str, StateHandler] = {
    "a robot with id 7 exists": _seed_robot_7,
}


def record_demo_pact(pact_dir: Path) -> Path:
    """Run the fulfillment service's expectations and freeze them as a pact."""
    app = create_app()
    _seed_robot_7(app)  # consumer designs the 'GET' interaction against known data
    client = make_sync_client(app, base_url="http://consumer.test")
    recorder = PactRecorder(
        client, consumer="fulfillment-service", provider="robot-registry"
    )
    recorder.record(
        "create a robot",
        "POST",
        "/robots",
        json_body={"sku": "NWR-PLT-2", "name": "Pallet Mover 2", "price_cents": 540000},
        expected_status=201,
        expect_subset={"sku": "NWR-PLT-2", "name": "Pallet Mover 2", "price_cents": 540000},
    )
    recorder.record(
        "fetch robot 7",
        "GET",
        "/robots/7",
        provider_state="a robot with id 7 exists",
        expected_status=200,
        expect_subset={"id": 7, "sku": "NWR-ARM-6", "name": "A6 Manipulator Arm"},
    )
    return recorder.write_pact(pact_dir / "fulfillment-service-robot-registry.json")
