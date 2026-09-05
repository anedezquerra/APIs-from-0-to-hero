"""Concurrency-anomaly demo: offset pagination duplicates, keyset does not.

A deterministic, single-threaded script that *interleaves* a reader (walking
pages of a parts list) with a writer (inserting cheap parts at the front of
the (unit_cost_cents, id) ordering between page fetches). This is exactly the
schedule two concurrent connections can produce; scripting it in one process
keeps the demo reproducible and offline.

Run:  python anomaly_demo.py
"""

from __future__ import annotations

import random
import sqlite3
from dataclasses import dataclass, field

DB = ":memory:"
PAGE = 5
TOTAL_PAGES = 4


def seed_catalog(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE parts ("
        " id INTEGER PRIMARY KEY, sku TEXT, unit_cost_cents INTEGER)"
    )
    rng = random.Random(7)
    rows = [
        (f"NWR-{i:05d}", 1000 + i * 100) for i in range(1, 21)
    ]
    del rng  # rows are literal: fully deterministic
    conn.executemany(
        "INSERT INTO parts (sku, unit_cost_cents) VALUES (?, ?)", rows
    )
    conn.commit()


@dataclass
class WalkResult:
    seen_ids: list[int] = field(default_factory=list)

    @property
    def duplicates(self) -> list[int]:
        seen: set[int] = set()
        dupes: list[int] = []
        for pid in self.seen_ids:
            if pid in seen and pid not in dupes:
                dupes.append(pid)
            seen.add(pid)
        return dupes


def writer_insert_cheap_part(conn: sqlite3.Connection, n: int) -> None:
    """Insert one part cheaper than everything else (lands at the front)."""
    conn.execute(
        "INSERT INTO parts (sku, unit_cost_cents) VALUES (?, ?)",
        (f"NWR-NEW-{n:02d}", 10 + n),
    )
    conn.commit()


def walk_offset(conn: sqlite3.Connection, writer: bool) -> WalkResult:
    """Paginate with LIMIT/OFFSET while the writer shifts the window."""
    result = WalkResult()
    for page_no in range(TOTAL_PAGES):
        rows = conn.execute(
            "SELECT id FROM parts ORDER BY unit_cost_cents, id "
            "LIMIT ? OFFSET ?",
            (PAGE, page_no * PAGE),
        ).fetchall()
        result.seen_ids.extend(r[0] for r in rows)
        if writer:
            # Between requests, another client inserts a cheap part.
            writer_insert_cheap_part(conn, page_no)
    return result


def walk_keyset(conn: sqlite3.Connection, writer: bool) -> WalkResult:
    """Paginate with a (cost, id) seek predicate under the same writer."""
    result = WalkResult()
    position: tuple[int, int] | None = None
    for page_no in range(TOTAL_PAGES):
        if position is None:
            rows = conn.execute(
                "SELECT id, unit_cost_cents FROM parts "
                "ORDER BY unit_cost_cents, id LIMIT ?",
                (PAGE,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, unit_cost_cents FROM parts "
                "WHERE (unit_cost_cents, id) > (?, ?) "
                "ORDER BY unit_cost_cents, id LIMIT ?",
                (position[0], position[1], PAGE),
            ).fetchall()
        result.seen_ids.extend(r[0] for r in rows)
        if rows:
            position = (int(rows[-1][1]), int(rows[-1][0]))
        if writer:
            writer_insert_cheap_part(conn, 100 + page_no)
    return result


def main() -> None:
    for strategy, walker in (("offset", walk_offset), ("keyset", walk_keyset)):
        conn = sqlite3.connect(DB)
        seed_catalog(conn)
        baseline = walker(conn, writer=False)
        conn.close()

        conn = sqlite3.connect(DB)
        seed_catalog(conn)
        shifted = walker(conn, writer=True)
        dupes = shifted.duplicates
        # Rows of the original catalog the reader *skipped* entirely.
        skipped = sorted(set(baseline.seen_ids) - set(shifted.seen_ids))
        print(
            f"{strategy:>7}: with concurrent inserts -> "
            f"duplicates={dupes or 'none'}, skipped={skipped or 'none'}"
        )
        conn.close()

    print(
        "Conclusion: offset windows are positional, so front inserts replay "
        "rows;\nkeyset windows are value-anchored, so the walk stays stable."
    )


if __name__ == "__main__":
    main()
