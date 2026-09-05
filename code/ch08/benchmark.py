"""Benchmark harness: offset vs keyset page-fetch latency at depth.

Measures the median wall-clock time to fetch one page of 50 rows at
increasing logical depths into the (unit_cost_cents, id) ordering.

Numbers are machine-dependent and therefore *illustrative*: the textbook
reports the shape of the curve, never a promised absolute latency.

Run:  python gen_dataset.py --rows 200000 --db parts.db
      python benchmark.py
"""

from __future__ import annotations

import sqlite3
import statistics
import time
from pathlib import Path

PAGE_SIZE = 50
REPEATS = 15
DEPTHS = [0, 1_000, 10_000, 50_000, 100_000, 150_000]

OFFSET_SQL = (
    "SELECT id, sku, name FROM parts "
    "ORDER BY unit_cost_cents, id LIMIT ? OFFSET ?"
)
KEYSET_SQL = (
    "SELECT id, sku, name FROM parts "
    "WHERE (unit_cost_cents, id) > (?, ?) "
    "ORDER BY unit_cost_cents, id LIMIT ?"
)


def time_query(conn: sqlite3.Connection, sql: str, params: tuple) -> float:
    """Return median seconds over REPEATS executions of one page fetch."""
    samples: list[float] = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        rows = conn.execute(sql, params).fetchall()
        samples.append(time.perf_counter() - start)
    assert len(rows) == PAGE_SIZE
    return statistics.median(samples)


def boundary_at(conn: sqlite3.Connection, depth: int) -> tuple[int, int]:
    """Return the (cost, id) tuple of the row at logical position ``depth``."""
    row = conn.execute(
        "SELECT unit_cost_cents, id FROM parts "
        "ORDER BY unit_cost_cents, id LIMIT 1 OFFSET ?",
        (depth,),
    ).fetchone()
    if row is None:
        raise ValueError(f"depth {depth} beyond table size")
    return int(row[0]), int(row[1])


def main() -> None:
    db = Path("parts.db")
    if not db.exists():
        raise SystemExit("parts.db missing; run gen_dataset.py first")
    conn = sqlite3.connect(db)
    try:
        total = conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
        print(f"rows={total:,}  page_size={PAGE_SIZE}  repeats={REPEATS}")
        print(f"{'depth':>8} | {'offset ms':>10} | {'keyset ms':>10} | speedup")
        print("-" * 48)
        for depth in DEPTHS:
            if depth + PAGE_SIZE >= total:
                continue
            cost, pid = boundary_at(conn, depth)
            t_offset = time_query(conn, OFFSET_SQL, (PAGE_SIZE, depth))
            t_keyset = time_query(conn, KEYSET_SQL, (cost, pid, PAGE_SIZE))
            ratio = t_offset / t_keyset if t_keyset else float("inf")
            print(
                f"{depth:>8,} | {t_offset * 1000:>10.3f} | "
                f"{t_keyset * 1000:>10.3f} | {ratio:>6.1f}x"
            )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
