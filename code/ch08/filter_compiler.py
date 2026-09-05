"""Allow-listed filter/sort compiler: query params -> parameterized SQL.

Grammar (public, documented surface):

    ?filter=unit_cost_cents:gte:500;category:eq:sensor;name:contains:servo
    ?sort=-unit_cost_cents,sku        (leading '-' means descending)

The compiler never interpolates user input into SQL text. It builds a small
AST of typed nodes, then renders that AST to a WHERE clause plus a bound
parameter list. Unknown fields, unknown operators, and type mismatches are
rejected with a descriptive ``FilterError`` -- clients get a 400, never a 500.

Offline demo:  python filter_compiler.py
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

# The public allow-list: API name -> (column, python type).
# Internal column names are deliberately *not* the public names everywhere:
# "cost" is the public name for the internal column unit_cost_cents.
ALLOWED_FIELDS: dict[str, tuple[str, type]] = {
    "sku": ("sku", str),
    "name": ("name", str),
    "category": ("category", str),
    "cost": ("unit_cost_cents", int),
    "weight": ("weight_grams", int),
    "active": ("active", bool),
}

ALLOWED_OPERATORS = {"eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"}
ORDERING_OPERATORS = {"gt", "gte", "lt", "lte"}


class FilterError(ValueError):
    """Raised for any filter/sort input outside the documented grammar."""


@dataclass(frozen=True)
class Comparison:
    field: str
    operator: Literal["eq", "ne", "gt", "gte", "lt", "lte"]
    value: Any


@dataclass(frozen=True)
class InList:
    field: str
    values: tuple[Any, ...]


@dataclass(frozen=True)
class Contains:
    field: str
    needle: str


@dataclass(frozen=True)
class SortKey:
    field: str
    descending: bool


FilterNode = Comparison | InList | Contains


def _coerce(field: str, raw: str) -> Any:
    column, kind = ALLOWED_FIELDS[field]
    del column  # coercion only needs the declared type
    try:
        if kind is bool:
            if raw.lower() not in {"true", "false"}:
                raise ValueError(raw)
            return 1 if raw.lower() == "true" else 0
        return kind(raw)
    except (TypeError, ValueError) as exc:
        raise FilterError(
            f"value {raw!r} is not a valid {kind.__name__} for field {field!r}"
        ) from exc


def parse_filter(expr: str) -> list[FilterNode]:
    """Parse the ``field:op:value[;field:op:value...]`` mini-grammar."""
    nodes: list[FilterNode] = []
    for clause in expr.split(";"):
        clause = clause.strip()
        if not clause:
            continue
        parts = clause.split(":", 2)
        if len(parts) != 3:
            raise FilterError(f"malformed clause {clause!r}; expected field:op:value")
        field, operator, raw = parts
        if field not in ALLOWED_FIELDS:
            raise FilterError(f"unknown field {field!r}; allowed: {sorted(ALLOWED_FIELDS)}")
        if operator not in ALLOWED_OPERATORS:
            raise FilterError(
                f"unknown operator {operator!r}; allowed: {sorted(ALLOWED_OPERATORS)}"
            )
        if operator == "in":
            values = tuple(_coerce(field, v) for v in raw.split(",") if v != "")
            if not values:
                raise FilterError("in operator requires at least one value")
            nodes.append(InList(field=field, values=values))
        elif operator == "contains":
            _, kind = ALLOWED_FIELDS[field]
            if kind is not str:
                raise FilterError(f"contains is only valid on text fields, not {field!r}")
            nodes.append(Contains(field=field, needle=raw))
        else:
            _, kind = ALLOWED_FIELDS[field]
            if kind is str and operator in ORDERING_OPERATORS:
                raise FilterError(f"operator {operator!r} is not valid on text field {field!r}")
            nodes.append(
                Comparison(field=field, operator=operator, value=_coerce(field, raw))
            )
    return nodes


def parse_sort(expr: str | None) -> list[SortKey]:
    """Parse ``-cost,sku`` into sort keys; always append the id tie-breaker."""
    keys: list[SortKey] = []
    if expr:
        for token in expr.split(","):
            token = token.strip()
            if not token:
                continue
            descending = token.startswith("-")
            field = token[1:] if descending else token
            if field not in ALLOWED_FIELDS:
                raise FilterError(f"cannot sort by unknown field {field!r}")
            keys.append(SortKey(field=field, descending=descending))
    # Deterministic tie-breaker: id is unique, so the total order is stable.
    keys.append(SortKey(field="id", descending=False))
    return keys


def compile_where(nodes: list[FilterNode]) -> tuple[str, list[Any]]:
    """Render filter nodes to a WHERE clause plus bound parameters."""
    fragments: list[str] = []
    params: list[Any] = []
    for node in nodes:
        column = ALLOWED_FIELDS[node.field][0]  # allow-list lookup, not input
        if isinstance(node, Comparison):
            symbol = {"eq": "=", "ne": "!=", "gt": ">", "gte": ">=", "lt": "<", "lte": "<="}[node.operator]
            fragments.append(f"{column} {symbol} ?")
            params.append(node.value)
        elif isinstance(node, InList):
            placeholders = ", ".join("?" for _ in node.values)
            fragments.append(f"{column} IN ({placeholders})")
            params.extend(node.values)
        elif isinstance(node, Contains):
            # Escape LIKE wildcards in user input; ESCAPE clause pins the marker.
            needle = node.needle.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            fragments.append(f"{column} LIKE ? ESCAPE '\\'")
            params.append(f"%{needle}%")
        else:  # pragma: no cover - exhaustive by construction
            raise FilterError(f"unsupported node {node!r}")
    clause = " AND ".join(fragments) if fragments else "1=1"
    return clause, params


def compile_query(
    filter_expr: str | None,
    sort_expr: str | None,
    limit: int,
) -> tuple[str, list[Any]]:
    """Compile public params into a complete, fully parameterized SELECT."""
    if limit < 1 or limit > 200:
        raise FilterError("limit must be between 1 and 200")
    nodes = parse_filter(filter_expr) if filter_expr else []
    where, params = compile_where(nodes)
    order = ", ".join(
        f"{ALLOWED_FIELDS.get(k.field, ('id',))[0]} {'DESC' if k.descending else 'ASC'}"
        for k in parse_sort(sort_expr)
    )
    sql = (
        "SELECT id, sku, name, category, unit_cost_cents, weight_grams, active "
        f"FROM parts WHERE {where} ORDER BY {order} LIMIT ?"
    )
    return sql, [*params, limit]


def _demo() -> None:
    db = Path("parts.db")
    if not db.exists():
        raise SystemExit("parts.db missing; run gen_dataset.py first")
    conn = sqlite3.connect(db)
    try:
        sql, params = compile_query(
            "cost:gte:500;category:in:sensor,actuator;name:contains:servo",
            "-cost,sku",
            limit=5,
        )
        print(f"SQL:    {sql}")
        print(f"params: {params}")
        for row in conn.execute(sql, params):
            print(row)

        for bad in (
            "password_hash:eq:x",   # unknown field (internal column leaked?)
            "cost:drop:1",          # unknown operator
            "cost:gte:abc",         # type mismatch
            "cost:eq:1;sort:evil",  # malformed clause
        ):
            try:
                compile_query(bad, None, 10)
            except FilterError as exc:
                print(f"rejected {bad!r}: {exc}")
            else:
                raise SystemExit(f"input {bad!r} should have been rejected")

        # Injection attempt is inert: it becomes a bound string parameter.
        sql, params = compile_query("name:eq:x' OR '1'='1", None, 5)
        rows = conn.execute(sql, params).fetchall()
        assert rows == [], "injection probe must match nothing"
        print("injection probe neutralized as bound parameter; demo OK")
    finally:
        conn.close()


if __name__ == "__main__":
    _demo()
