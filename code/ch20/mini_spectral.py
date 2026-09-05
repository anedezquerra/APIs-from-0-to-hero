r"""mini_spectral.py -- a miniature Spectral-style OpenAPI linter.

Loads an OpenAPI YAML document and a ruleset expressed as data (YAML),
evaluates every rule, reports violations with JSON paths, and returns a
CI-friendly exit code:

    0 -- no error-severity violations
    1 -- at least one error-severity violation
    2 -- usage error, unreadable file, or malformed document/ruleset

Usage (PowerShell):
    python mini_spectral.py .\specs\northwind_robots.yaml --ruleset .\ruleset.yaml
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import yaml

HTTP_METHODS = frozenset(
    {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
)

CASING_PATTERNS: dict[str, re.Pattern[str]] = {
    "kebab": re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$"),
    "snake": re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$"),
    "camel": re.compile(r"^[a-z][a-zA-Z0-9]*$"),
}

SEVERITIES = ("error", "warn")


@dataclass(frozen=True)
class Violation:
    """A single rule breach located by a JSON-path-ish string."""

    rule_id: str
    severity: str
    path: str
    message: str

    def render(self) -> str:
        return (
            f"[{self.severity.upper():5}] {self.rule_id} "
            f"at {self.path}: {self.message}"
        )


# --------------------------------------------------------------------------
# Document navigation helpers
# --------------------------------------------------------------------------

def resolve_pointer(doc: Any, pointer: str) -> Any:
    """Resolve a minimal JSON Pointer ('/info/contact'); None if absent."""
    node = doc
    for token in pointer.strip("/").split("/"):
        if not isinstance(node, dict) or token not in node:
            return None
        node = node[token]
    return node


def json_path(*parts: str) -> str:
    """Build a readable JSON path, quoting keys that contain slashes."""
    out = "$"
    for part in parts:
        if re.fullmatch(r"[A-Za-z0-9_-]+", part):
            out += f".{part}"
        else:
            out += f'["{part}"]'
    return out


def iter_operations(doc: dict[str, Any]):
    """Yield (json_path, path_key, method, operation) for every operation."""
    paths = doc.get("paths") or {}
    if not isinstance(paths, dict):
        return
    for path_key, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() in HTTP_METHODS and isinstance(operation, dict):
                yield (
                    json_path("paths", path_key, method.lower()),
                    path_key,
                    method.lower(),
                    operation,
                )


# --------------------------------------------------------------------------
# Rule kinds -- each takes (doc, rule) and yields Violations
# --------------------------------------------------------------------------

def check_require_field(
    doc: dict[str, Any], rule: dict[str, Any]
) -> list[Violation]:
    pointer = str(rule["pointer"])
    if resolve_pointer(doc, pointer) is None:
        return [
            Violation(
                rule["id"],
                rule["severity"],
                "$" + pointer.replace("/", "."),
                rule["message"],
            )
        ]
    return []


def check_match(doc: dict[str, Any], rule: dict[str, Any]) -> list[Violation]:
    pointer = str(rule["pointer"])
    value = resolve_pointer(doc, pointer)
    pattern = re.compile(str(rule["pattern"]))
    if value is None or not pattern.fullmatch(str(value)):
        return [
            Violation(
                rule["id"],
                rule["severity"],
                "$" + pointer.replace("/", "."),
                f"{rule['message']} (found: {value!r})",
            )
        ]
    return []


def check_casing(doc: dict[str, Any], rule: dict[str, Any]) -> list[Violation]:
    style = str(rule["style"])
    pattern = CASING_PATTERNS[style]
    violations: list[Violation] = []

    if rule["target"] == "operation_id":
        for op_path, _pk, _m, operation in iter_operations(doc):
            op_id = operation.get("operationId")
            if op_id is None or not pattern.fullmatch(str(op_id)):
                violations.append(
                    Violation(
                        rule["id"],
                        rule["severity"],
                        f"{op_path}.operationId",
                        f"{rule['message']} (found: {op_id!r})",
                    )
                )
    elif rule["target"] == "path_segment":
        paths = doc.get("paths") or {}
        for path_key in paths:
            for segment in str(path_key).split("/"):
                if not segment or (segment.startswith("{") and segment.endswith("}")):
                    continue
                if not pattern.fullmatch(segment):
                    violations.append(
                        Violation(
                            rule["id"],
                            rule["severity"],
                            json_path("paths", path_key),
                            f"{rule['message']} (segment: {segment!r})",
                        )
                    )
    else:  # defensive: ruleset is data too, and data can be wrong
        raise ValueError(f"unknown casing target: {rule['target']!r}")
    return violations


def check_problem_json_errors(
    doc: dict[str, Any], rule: dict[str, Any]
) -> list[Violation]:
    violations = []
    for op_path, _pk, _m, operation in iter_operations(doc):
        responses = operation.get("responses") or {}
        ok = False
        for status, response in responses.items():
            code = str(status)
            if not (code.startswith(("4", "5")) or code == "default"):
                continue
            content = (response or {}).get("content") or {}
            if "application/problem+json" in content:
                ok = True
                break
        if not ok:
            violations.append(
                Violation(
                    rule["id"],
                    rule["severity"],
                    f"{op_path}.responses",
                    rule["message"],
                )
            )
    return violations


def check_pagination_required(
    doc: dict[str, Any], rule: dict[str, Any]
) -> list[Violation]:
    required_params = [str(p) for p in rule.get("params", ["limit", "cursor"])]
    violations = []
    for op_path, path_key, method, operation in iter_operations(doc):
        is_collection_get = method == "get" and not str(path_key).rstrip("/").endswith("}")
        if not is_collection_get:
            continue
        present = {
            str(p.get("name"))
            for p in operation.get("parameters") or []
            if isinstance(p, dict) and p.get("in") == "query"
        }
        missing = [p for p in required_params if p not in present]
        if missing:
            violations.append(
                Violation(
                    rule["id"],
                    rule["severity"],
                    f"{op_path}.parameters",
                    f"{rule['message']} (missing: {', '.join(missing)})",
                )
            )
    return violations


RULE_KINDS: dict[
    str, Callable[[dict[str, Any], dict[str, Any]], list[Violation]]
] = {
    "require-field": check_require_field,
    "match": check_match,
    "casing": check_casing,
    "problem-json-errors": check_problem_json_errors,
    "pagination-required": check_pagination_required,
}


# --------------------------------------------------------------------------
# Engine
# --------------------------------------------------------------------------

def load_yaml_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def lint(spec: dict[str, Any], ruleset: dict[str, Any]) -> list[Violation]:
    """Evaluate every rule in the ruleset against the spec document."""
    if not isinstance(spec, dict) or "openapi" not in spec:
        raise ValueError("document does not look like an OpenAPI spec")
    rules = (ruleset or {}).get("rules") or []
    violations: list[Violation] = []
    for rule in rules:
        kind = rule.get("kind")
        handler = RULE_KINDS.get(str(kind))
        if handler is None:
            raise ValueError(f"unknown rule kind: {kind!r}")
        if rule.get("severity") not in SEVERITIES:
            raise ValueError(f"rule {rule.get('id')!r}: bad severity")
        violations.extend(handler(spec, rule))
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mini Spectral-style linter.")
    parser.add_argument("spec", type=Path, help="OpenAPI YAML file")
    parser.add_argument(
        "--ruleset", type=Path, required=True, help="Ruleset YAML file"
    )
    args = parser.parse_args(argv)

    try:
        spec = load_yaml_file(args.spec)
        ruleset = load_yaml_file(args.ruleset)
    except (OSError, yaml.YAMLError) as exc:
        print(f"error: cannot load input: {exc}", file=sys.stderr)
        return 2

    try:
        violations = lint(spec, ruleset)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for violation in violations:
        print(violation.render())

    errors = sum(1 for v in violations if v.severity == "error")
    warnings = sum(1 for v in violations if v.severity == "warn")
    print(f"\n{args.spec.name}: {errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
