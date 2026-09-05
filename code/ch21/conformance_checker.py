"""Architecture conformance checker (Chapter 21).

Turns the book's governance rules into executable policy. Given a
manifests folder of OpenAPI (YAML/JSON) and AsyncAPI documents, the
checker verifies the platform invariants that Chapter 20 establishes
as linted, CI-enforced rules:

* O-001: every spec declares a security scheme with a non-empty
  ``description`` and applies ``security`` globally.
* O-002: every 4xx/5xx response references the shared
  ``ProblemDetails`` component (RFC 9457).
* O-003: every collection GET documents ``limit`` and ``cursor``
  query parameters and a ``nextCursor`` response field.
* O-004: the ``info.version`` header version matches
  ``YYYY-MM-DD`` (the platform's date-based versioning rule).
* A-001: every AsyncAPI publish payload message defines ``event_id``
  and ``occurred_at`` (the platform's event envelope).

Offline, deterministic. Requires only PyYAML. Python 3.11+.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DATE_VERSION = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ENVELOPE_FIELDS = ("event_id", "occurred_at")


@dataclass(frozen=True)
class Violation:
    """A single governance rule breach in one manifest."""

    rule: str
    spec: str
    detail: str

    def render(self) -> str:
        return f"[{self.rule}] {self.spec}: {self.detail}"


def _load_specs(folder: Path) -> dict[str, Any]:
    specs: dict[str, Any] = {}
    for path in sorted(folder.rglob("*")):
        if path.suffix.lower() in {".yaml", ".yml", ".json"}:
            specs[str(path.relative_to(folder))] = yaml.safe_load(
                path.read_text(encoding="utf-8")
            )
    return specs


def _resolve_local_ref(document: Any, node: Any, depth: int = 0) -> Any:
    """Resolve one local ``#/...`` reference against its own document."""
    if depth > 10 or not isinstance(node, dict) or "$ref" not in node:
        return node
    ref = str(node["$ref"])
    if not ref.startswith("#/"):
        return node  # external refs are out of scope for the offline checker
    target: Any = document
    for part in ref[2:].split("/"):
        if not isinstance(target, dict) or part not in target:
            return node
        target = target[part]
    return _resolve_local_ref(document, target, depth + 1)


def _schema_has_property(document: Any, schema: Any, name: str) -> bool:
    """True when ``name`` appears in the schema or any composed/ref'd part."""
    schema = _resolve_local_ref(document, schema)
    if not isinstance(schema, dict):
        return False
    if name in (schema.get("properties") or {}):
        return True
    for key in ("allOf", "anyOf", "oneOf"):
        if any(
            _schema_has_property(document, part, name) for part in schema.get(key, [])
        ):
            return True
    return False


def _collect_refs(document: Any, schema: Any, depth: int = 0) -> list[str]:
    """Collect every ``$ref`` target reachable from a schema (any depth)."""
    schema = _resolve_local_ref(document, schema)
    if depth > 10 or not isinstance(schema, dict):
        return []
    refs: list[str] = []
    raw = schema.get("$ref")
    if isinstance(raw, str):
        refs.append(raw)
    for key in ("allOf", "anyOf", "oneOf"):
        for part in schema.get(key, []):
            refs.extend(_collect_refs(document, part, depth + 1))
    return refs


def _content_schemas(content: Any) -> list[Any]:
    if not isinstance(content, dict):
        return []
    return [media.get("schema") for media in content.values() if isinstance(media, dict)]


def _check_openapi(name: str, spec: Any) -> list[Violation]:
    violations: list[Violation] = []
    if not isinstance(spec, dict) or "openapi" not in spec:
        return violations

    # O-001: auth scheme presence and global security requirement.
    schemes = (
        (spec.get("components") or {}).get("securitySchemes") or {}
    )
    if not schemes:
        violations.append(Violation("O-001", name, "no securitySchemes defined"))
    for scheme_name, scheme in schemes.items():
        if not (scheme or {}).get("description"):
            violations.append(
                Violation("O-001", name, f"scheme {scheme_name!r} lacks a description")
            )
    if not spec.get("security"):
        violations.append(
            Violation("O-001", name, "no global security requirement applied")
        )

    # O-002: error responses must reference ProblemDetails.
    paths = spec.get("paths") or {}
    for path, item in paths.items():
        for method, operation in (item or {}).items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            responses = (operation or {}).get("responses") or {}
            for status, response in responses.items():
                if not str(status).startswith(("4", "5")):
                    continue
                schemas = _content_schemas((response or {}).get("content"))
                refs: list[str] = []
                for schema in schemas:
                    raw = (schema or {}).get("$ref") if isinstance(schema, dict) else None
                    if raw:
                        refs.append(raw)
                    else:
                        refs.extend(_collect_refs(spec, schema))
                if not any(r.endswith("/ProblemDetails") for r in refs):
                    violations.append(
                        Violation(
                            "O-002",
                            name,
                            f"{method.upper()} {path} {status} does not reference "
                            "ProblemDetails",
                        )
                    )

    # O-003: collection GETs must document limit/cursor pagination.
    for path, item in paths.items():
        get_op = (item or {}).get("get")
        if not get_op or not path.rstrip("/").endswith("s"):
            continue
        params = {
            (p or {}).get("name")
            for p in get_op.get("parameters") or []
            if isinstance(p, dict) and p.get("in") == "query"
        }
        missing = {"limit", "cursor"} - params
        if missing:
            violations.append(
                Violation(
                    "O-003",
                    name,
                    f"GET {path} missing query params: {sorted(missing)}",
                )
            )
        ok_schemas = _content_schemas(
            ((get_op.get("responses") or {}).get("200") or {}).get("content")
        )
        if not any(
            _schema_has_property(spec, s, "nextCursor") for s in ok_schemas
        ):
            violations.append(
                Violation("O-003", name, f"GET {path} 200 schema lacks nextCursor")
            )

    # O-004: date-based version header convention.
    version = str((spec.get("info") or {}).get("version", ""))
    if not DATE_VERSION.match(version):
        violations.append(
            Violation(
                "O-004",
                name,
                f"info.version {version!r} is not a YYYY-MM-DD date version",
            )
        )
    return violations


def _check_asyncapi(name: str, spec: Any) -> list[Violation]:
    violations: list[Violation] = []
    if not isinstance(spec, dict) or "asyncapi" not in spec:
        return violations
    channels = spec.get("channels") or {}
    for channel, item in channels.items():
        publish = (item or {}).get("publish")
        if not publish:
            continue
        message = _resolve_local_ref(spec, publish.get("message") or {})
        payload = _resolve_local_ref(spec, (message or {}).get("payload") or {})
        missing = [
            f for f in ENVELOPE_FIELDS if not _schema_has_property(spec, payload, f)
        ]
        if missing:
            violations.append(
                Violation(
                    "A-001",
                    name,
                    f"channel {channel!r} publish payload missing envelope "
                    f"fields: {missing}",
                )
            )
    return violations


def check_folder(folder: Path) -> list[Violation]:
    """Check every spec under ``folder`` and return all violations."""
    specs = _load_specs(folder)
    if not specs:
        raise FileNotFoundError(f"no YAML/JSON manifests found under {folder}")
    violations: list[Violation] = []
    for name, spec in specs.items():
        violations.extend(_check_openapi(name, spec))
        violations.extend(_check_asyncapi(name, spec))
    return violations


def main(argv: list[str]) -> int:
    folder = Path(argv[1]) if len(argv) > 1 else Path("manifests")
    try:
        violations = check_folder(folder)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if violations:
        print(f"FAIL: {len(violations)} governance violation(s)")
        for v in violations:
            print(f"  {v.render()}")
        return 1
    print(f"PASS: all governance invariants hold under {folder}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
