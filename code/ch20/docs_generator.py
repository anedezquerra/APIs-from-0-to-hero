r"""docs_generator.py -- render an OpenAPI YAML spec as Markdown reference docs.

Stdlib + PyYAML only. Docs-as-code in miniature: the spec is the single
source of truth and the rendered reference is a build artifact, so docs
can never drift from the contract without the build noticing.

Usage (PowerShell):
    python docs_generator.py .\specs\northwind_robots.yaml
    python docs_generator.py .\specs\northwind_robots.yaml --out fleet-api.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

HTTP_METHODS = ("get", "put", "post", "delete", "patch", "options", "head")


def schema_type(schema: dict[str, Any]) -> str:
    """Human-readable type label, resolving local $refs to their name."""
    if "$ref" in schema:
        return str(schema["$ref"]).rsplit("/", 1)[-1]
    base = schema.get("type", "any")
    if base == "array":
        return f"array[{schema_type(schema.get('items') or {})}]"
    if "enum" in schema:
        return "enum(" + ", ".join(str(v) for v in schema["enum"]) + ")"
    if "format" in schema:
        return f"{base} ({schema['format']})"
    return str(base)


def render_parameters(operation: dict[str, Any]) -> list[str]:
    params = operation.get("parameters") or []
    if not params:
        return []
    lines = [
        "",
        "| Name | In | Required | Type |",
        "|---|---|---|---|",
    ]
    for param in params:
        schema = param.get("schema") or {}
        lines.append(
            f"| `{param.get('name', '?')}` | {param.get('in', '?')} | "
            f"{'yes' if param.get('required') else 'no'} | "
            f"{schema_type(schema)} |"
        )
    return lines


def render_responses(operation: dict[str, Any]) -> list[str]:
    responses = operation.get("responses") or {}
    lines = ["", "| Status | Meaning | Body |", "|---|---|---|"]
    for status, response in responses.items():
        content = (response or {}).get("content") or {}
        bodies = ", ".join(
            f"{media} -> {schema_type((cfg or {}).get('schema') or {})}"
            for media, cfg in content.items()
        ) or "-"
        lines.append(
            f"| `{status}` | {(response or {}).get('description', '')} "
            f"| {bodies} |"
        )
    return lines


def render_example(operation: dict[str, Any]) -> list[str]:
    """Emit the first response example found, as a fenced JSON block."""
    for _status, response in (operation.get("responses") or {}).items():
        for _media, cfg in ((response or {}).get("content") or {}).items():
            if isinstance(cfg, dict) and "example" in cfg:
                return [
                    "",
                    "Example:",
                    "",
                    "```json",
                    json.dumps(cfg["example"], indent=2),
                    "```",
                ]
    return []


def render_markdown(spec: dict[str, Any]) -> str:
    info = spec.get("info") or {}
    lines: list[str] = [
        f"# {info.get('title', 'Untitled API')}",
        "",
        f"**Version:** {info.get('version', 'n/a')}",
        "",
        (info.get("description") or "").strip(),
        "",
    ]
    for server in spec.get("servers") or []:
        lines.append(f"- Server: `{server.get('url')}` "
                     f"({server.get('description', '')})")
    lines.append("")
    lines.append("## Endpoints")

    paths = spec.get("paths") or {}
    for path_key, path_item in paths.items():
        for method in HTTP_METHODS:
            operation = (path_item or {}).get(method)
            if not isinstance(operation, dict):
                continue
            lines += [
                "",
                f"### `{method.upper()} {path_key}`",
                "",
                operation.get("summary", ""),
            ]
            lines += render_parameters(operation)
            lines += render_responses(operation)
            lines += render_example(operation)
            lines.append("")

    schemas = ((spec.get("components") or {}).get("schemas")) or {}
    if schemas:
        lines.append("## Schemas")
    for name, schema in schemas.items():
        required = set(schema.get("required") or [])
        lines += [
            "",
            f"### {name}",
            "",
            "| Property | Type | Required | Notes |",
            "|---|---|---|---|",
        ]
        for prop, prop_schema in (schema.get("properties") or {}).items():
            notes = prop_schema.get("description", "")
            if "x-classification" in prop_schema:
                notes = (notes + " " if notes else "") + (
                    f"[classification: {prop_schema['x-classification']}]"
                )
            lines.append(
                f"| `{prop}` | {schema_type(prop_schema)} | "
                f"{'yes' if prop in required else 'no'} | {notes} |"
            )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OpenAPI -> Markdown docs.")
    parser.add_argument("spec", type=Path, help="OpenAPI YAML file")
    parser.add_argument("--out", type=Path, default=None,
                        help="Write Markdown here (default: stdout)")
    args = parser.parse_args(argv)

    try:
        spec = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(f"error: cannot load spec: {exc}", file=sys.stderr)
        return 2
    if not isinstance(spec, dict) or "openapi" not in spec:
        print("error: not an OpenAPI document", file=sys.stderr)
        return 2

    markdown = render_markdown(spec)
    if args.out:
        args.out.write_text(markdown, encoding="utf-8")
        print(f"wrote {args.out} ({len(markdown)} chars)")
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
