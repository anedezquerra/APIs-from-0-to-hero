"""Deterministic synthetic dataset generator for Chapter 8.

Generates the fictional *Northwind Robotics* parts catalog into a local
SQLite database. Offline-first: no network, no third-party packages.

Usage (PowerShell):
    python gen_dataset.py --rows 200000 --db parts.db
"""

from __future__ import annotations

import argparse
import random
import sqlite3
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS parts (
    id              INTEGER PRIMARY KEY,
    sku             TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    category        TEXT NOT NULL,
    unit_cost_cents INTEGER NOT NULL,
    weight_grams    INTEGER NOT NULL,
    active          INTEGER NOT NULL,
    updated_at      TEXT NOT NULL
);
-- Composite index aligned with the keyset ordering (unit_cost_cents, id).
CREATE INDEX IF NOT EXISTS idx_parts_cost_id
    ON parts (unit_cost_cents, id);
-- Composite index aligned with (category, unit_cost_cents, id) keysets.
CREATE INDEX IF NOT EXISTS idx_parts_cat_cost_id
    ON parts (category, unit_cost_cents, id);
"""

CATEGORIES: list[str] = [
    "actuator", "sensor", "chassis", "drivetrain", "power",
    "controller", "fastener", "optic",
]

NAME_PARTS: list[str] = [
    "servo", "gyro", "lidar", "torque", "chassis", "rail", "bearing",
    "gearbox", "battery", "inverter", "encoder", "bracket", "harness",
]

NAME_SUFFIXES: list[str] = [
    "Alpha", "Beta", "Prime", "XL", "Micro", "HD", "Mk2", "Pro",
]


def generate_rows(count: int, seed: int) -> list[tuple]:
    """Build ``count`` deterministic synthetic part rows."""
    rng = random.Random(seed)
    rows: list[tuple] = []
    for i in range(1, count + 1):
        name = f"{rng.choice(NAME_PARTS)}-{rng.choice(NAME_SUFFIXES)}"
        category = rng.choice(CATEGORIES)
        # Skewed cost distribution: many cheap parts, few expensive ones.
        cost = int(rng.expovariate(1 / 4000.0)) + 50
        weight = rng.randint(2, 25_000)
        active = 1 if rng.random() < 0.93 else 0
        # Deterministic pseudo-timestamp derived from the row number only.
        minute = (i * 7) % (60 * 24 * 365)
        updated = f"2025-01-01T00:00:00Z+{minute:07d}m"
        rows.append((f"NWR-{i:07d}", name, category, cost, weight, active, updated))
    return rows


def build_database(db_path: Path, rows: int, seed: int) -> None:
    """Create (or replace) the SQLite database with ``rows`` parts."""
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)
        started = time.perf_counter()
        data = generate_rows(rows, seed)
        with conn:
            conn.executemany(
                "INSERT INTO parts "
                "(sku, name, category, unit_cost_cents, weight_grams, "
                " active, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                data,
            )
        conn.execute("ANALYZE")
        conn.commit()
        elapsed = time.perf_counter() - started
        count = conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
        print(f"generated {count:,} rows into {db_path} in {elapsed:.2f}s")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=200_000)
    parser.add_argument("--db", type=Path, default=Path("parts.db"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.rows < 1:
        raise SystemExit("--rows must be >= 1")
    build_database(args.db, args.rows, args.seed)


if __name__ == "__main__":
    main()
