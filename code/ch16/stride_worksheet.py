"""STRIDE worksheet generator.

Reads an OpenAPI 3.x document (JSON or the small YAML subset PyYAML-free
tooling can handle: pass pre-parsed dicts) and emits a per-endpoint threat
checklist skeleton. Pure stdlib, offline, deterministic: endpoints are
sorted, heuristics are explicit rules you can audit.
"""

from __future__ import annotations

import json
from typing import Any, Iterable

STRIDE = ("Spoofing", "Tampering", "Repudiation", "Information Disclosure",
          "Denial of Service", "Elevation of Privilege")

WRITE_METHODS = {"post", "put", "patch", "delete"}
ADMIN_HINTS = ("/admin", "/internal", "/debug")
ID_PARAM_HINTS = ("{id}", "{robot_id}", "{user_id}", "{order_id}")


def _heuristics(method: str, path: str, operation: dict[str, Any]) -> dict[str, list[str]]:
    """Flag the STRIDE categories that need human attention and why."""
    flagged: dict[str, list[str]] = {s: [] for s in STRIDE}
    secured = bool(operation.get("security"))
    has_id = any(hint in path for hint in ID_PARAM_HINTS) or any(
        p.get("in") == "path" and str(p.get("name", "")).endswith("id")
        for p in operation.get("parameters", [])
    )
    if not secured:
        flagged["Spoofing"].append("no security scheme declared on operation")
    if has_id:
        flagged["Information Disclosure"].append(
            "path id present: verify object-level authorization (BOLA)"
        )
        flagged["Tampering"].append(
            "path id present: confirm ids are not enumerable or are scoped"
        )
    if method in WRITE_METHODS:
        flagged["Tampering"].append(
            "write method: schema must forbid server-owned fields (mass assignment)"
        )
        flagged["Repudiation"].append(
            "write method: require an audit record with actor, before/after"
        )
    if any(hint in path for hint in ADMIN_HINTS):
        flagged["Elevation of Privilege"].append(
            "admin/internal surface: function-level role check required"
        )
    responses = operation.get("responses", {})
    if "429" not in responses:
        flagged["Denial of Service"].append(
            "no 429 documented: confirm rate/size limits exist"
        )
    if method == "get":
        flagged["Information Disclosure"].append(
            "read method: review response fields for excessive data exposure"
        )
    return {k: v for k, v in flagged.items() if v}


def generate_worksheet(spec: dict[str, Any]) -> str:
    """Emit a Markdown STRIDE checklist skeleton, one block per endpoint."""
    title = spec.get("info", {}).get("title", "Untitled API")
    lines = [
        f"# STRIDE Worksheet -- {title}",
        "",
        "Fill one row per flagged category: threat, abuse case, mitigation,",
        "detection signal, owner, status.",
        "",
    ]
    for path in sorted(spec.get("paths", {})):
        for method in sorted(spec["paths"][path]):
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            operation = spec["paths"][path][method]
            summary = operation.get("summary", "")
            lines.append(f"## {method.upper()} {path}")
            if summary:
                lines.append(f"_{summary}_")
            lines.append("")
            flagged = _heuristics(method, path, operation)
            if not flagged:
                lines.append("- [ ] No heuristic flags; still review manually.")
            for category in STRIDE:
                for reason in flagged.get(category, []):
                    lines.append(f"- [ ] **{category}** -- {reason}")
            lines.append("")
            lines.append("| STRIDE | Threat | Abuse case | Mitigation | Detection | Owner | Status |")
            lines.append("|---|---|---|---|---|---|---|")
            for category in STRIDE:
                mark = "FLAGGED" if category in flagged else ""
                lines.append(f"| {category} | {mark} | | | | | |")
            lines.append("")
    return "\n".join(lines)


def load_spec(path: str) -> dict[str, Any]:
    """Load an OpenAPI document from a JSON file."""
    with open(path, encoding="utf-8") as handle:
        data: dict[str, Any] = json.load(handle)
    if "paths" not in data:
        raise ValueError("not an OpenAPI document: missing 'paths'")
    return data


def main(argv: Iterable[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="OpenAPI -> STRIDE worksheet")
    parser.add_argument("spec", help="path to an OpenAPI JSON document")
    parser.add_argument("-o", "--out", default=None, help="output .md path")
    args = parser.parse_args(list(argv) if argv is not None else None)
    worksheet = generate_worksheet(load_spec(args.spec))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(worksheet)
    else:
        print(worksheet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
