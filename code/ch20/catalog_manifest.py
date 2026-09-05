r"""catalog_manifest.py -- generate Backstage-style API catalog entries.

Scans a directory of OpenAPI YAML specs and emits one catalog manifest
document per spec (apiVersion backstage.io/v1alpha1, kind: API), with
ownership and lifecycle read from the spec's info.x-lifecycle block so
the catalog, like the docs, is generated from the contract rather than
maintained by hand.

Usage (PowerShell):
    python catalog_manifest.py .\specs
    python catalog_manifest.py .\specs --out catalog-apis.yaml
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

DEFAULT_OWNER = "platform-team"
DEFAULT_LIFECYCLE = "production"


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "unnamed-api"


def manifest_for(spec_path: Path, spec: dict[str, Any], root: Path) -> dict[str, Any]:
    info = spec.get("info") or {}
    lifecycle_block = info.get("x-lifecycle") or {}
    rel_path = spec_path.relative_to(root.parent).as_posix()
    return {
        "apiVersion": "backstage.io/v1alpha1",
        "kind": "API",
        "metadata": {
            "name": slugify(str(info.get("title", spec_path.stem))),
            "description": " ".join(
                str(info.get("description", "")).split()
            )[:200],
            "annotations": {
                "northwind/spec-version": str(info.get("version", "0.0.0")),
            },
        },
        "spec": {
            "type": "openapi",
            "lifecycle": str(lifecycle_block.get("state", DEFAULT_LIFECYCLE)),
            "owner": str(lifecycle_block.get("owner", DEFAULT_OWNER)),
            "definition": {"$text": f"./{rel_path}"},
        },
    }


def scan(spec_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    manifests: list[dict[str, Any]] = []
    warnings: list[str] = []
    candidates = sorted(
        [*spec_dir.glob("*.yaml"), *spec_dir.glob("*.yml")]
    )
    if not candidates:
        warnings.append(f"no .yaml/.yml files found in {spec_dir}")
    for spec_path in candidates:
        try:
            spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            warnings.append(f"{spec_path.name}: YAML parse error: {exc}")
            continue
        if not isinstance(spec, dict) or "openapi" not in spec:
            warnings.append(f"{spec_path.name}: not an OpenAPI doc, skipped")
            continue
        manifests.append(manifest_for(spec_path, spec, spec_dir))
    return manifests, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emit Backstage-style API manifests for a spec folder."
    )
    parser.add_argument("spec_dir", type=Path, help="directory of OpenAPI YAML")
    parser.add_argument("--out", type=Path, default=None,
                        help="write manifests here (default: stdout)")
    args = parser.parse_args(argv)

    if not args.spec_dir.is_dir():
        print(f"error: not a directory: {args.spec_dir}", file=sys.stderr)
        return 2

    manifests, warnings = scan(args.spec_dir)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    text = "---\n" + "---\n".join(
        yaml.safe_dump(m, sort_keys=False) for m in manifests
    )
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {len(manifests)} manifest(s) to {args.out}")
    else:
        print(text, end="")
    return 0 if manifests else 1


if __name__ == "__main__":
    raise SystemExit(main())
