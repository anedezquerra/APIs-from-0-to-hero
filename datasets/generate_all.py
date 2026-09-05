#!/usr/bin/env python3
"""Deterministic synthetic dataset generator for the "Northwind Robotics" universe.

Book: "Mastering APIs: From Zero to Production Guru".
Regenerates every file under ``datasets\\northwind_robotics\\`` byte-for-byte.

Everything is synthetic: fictional people, ``example.invalid`` emails, test-only
signing keys. No network access, standard library only (Python 3.11+).

Usage (PowerShell, from the repository root):

    # Generate (or regenerate) all datasets
    python .\\datasets\\generate_all.py

    # CI check: verify committed files match regeneration, exit 1 on drift
    python .\\datasets\\generate_all.py --check

Determinism / byte-stability notes:
  * Single ``random.Random(42)`` instance threaded through all generators in a
    fixed call order.
  * All output is UTF-8 with ``\\n`` newlines; files are written as raw bytes so
    Windows newline translation can never interfere.
  * Timestamps are ISO-8601 UTC (``...Z``).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import io
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED = 42
ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "northwind_robotics"

# TEST-ONLY webhook signing key (chapter 11 labs). Not a real secret.
WEBHOOK_SIGNING_KEY = b"whsec_test_northwind_robotics_0123456789abcdef"

EPOCH = datetime(2020, 1, 1, tzinfo=timezone.utc)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def iso(dt: datetime) -> str:
    """ISO-8601 UTC timestamp with Z suffix (second precision)."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rand_ts(rng: random.Random, start: datetime, end: datetime) -> datetime:
    span = int((end - start).total_seconds())
    return start + timedelta(seconds=rng.randrange(span))


def csv_bytes(header: list[str], rows: list[list[object]]) -> bytes:
    buf = io.StringIO(newline="")
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def jsonl_bytes(records: list[dict]) -> bytes:
    lines = [json.dumps(r, separators=(",", ":")) for r in records]
    return ("\n".join(lines) + "\n").encode("utf-8")


def txt_bytes(text: str) -> bytes:
    """Encode embedded text with normalized LF newlines regardless of how this
    source file itself was checked out (CRLF/ LF) on disk."""
    return text.replace("\r\n", "\n").encode("utf-8")


# --------------------------------------------------------------------------- #
# Static reference pools (all fictional)
# --------------------------------------------------------------------------- #

WAREHOUSES: list[tuple[str, str, str, str, str, int]] = [
    # warehouse_id, code, name, city, country, capacity_m2
    ("W-01", "DET", "Motor City Depot", "Detroit", "United States", 42000),
    ("W-02", "RDM", "Rainier Distribution Hub", "Redmond", "United States", 28000),
    ("W-03", "GDL", "Jalisco Robotics Center", "Guadalajara", "Mexico", 21000),
    ("W-04", "HAM", "Hanseatic Logistics Park", "Hamburg", "Germany", 35000),
    ("W-05", "WAW", "Vistula Fulfillment Site", "Warsaw", "Poland", 19000),
    ("W-06", "OSA", "Kansai Automation Depot", "Osaka", "Japan", 26000),
    ("W-07", "SIN", "Straits Regional Hub", "Singapore", "Singapore", 17000),
    ("W-08", "SYD", "Harbour Spares Facility", "Sydney", "Australia", 14000),
]

# category_code -> (category, [subcategories], (min_price_cents, max_price_cents),
#                   (min_weight_g, max_weight_g))
CATEGORIES: dict[str, tuple[str, list[str], tuple[int, int], tuple[int, int]]] = {
    "ACT": ("Actuators", ["Servo Motor", "Linear Actuator", "Rotary Actuator", "Stepper Motor"], (15000, 450000), (400, 22000)),
    "SEN": ("Sensors", ["LIDAR Unit", "Force-Torque Sensor", "Proximity Sensor", "Rotary Encoder", "Thermal Camera Module"], (8000, 300000), (25, 3500)),
    "CTL": ("Controllers", ["Motion Controller", "PLC Module", "Edge Compute Node", "IO Expansion Board"], (25000, 900000), (300, 9000)),
    "PWR": ("Power Systems", ["Battery Pack", "Power Supply Unit", "Motor Driver", "DC-DC Converter"], (5000, 250000), (200, 18000)),
    "FRM": ("Frames and Structure", ["Aluminum Extrusion", "Base Plate", "Gantry Beam", "Mounting Bracket"], (2000, 80000), (500, 60000)),
    "EFF": ("End Effectors", ["Parallel Gripper", "Vacuum Gripper", "Welding Torch", "Tool Changer"], (10000, 500000), (150, 12000)),
    "DRV": ("Drivetrain", ["Harmonic Reducer", "Planetary Gearbox", "Timing Belt", "Ball Screw"], (6000, 350000), (100, 15000)),
    "CBL": ("Cabling and Connectors", ["Cable Chain", "M12 Connector", "Servo Cable", "EtherCAT Cable"], (300, 15000), (10, 4000)),
}

PART_ADJECTIVES = [
    "Precision", "Heavy-Duty", "Compact", "Industrial", "High-Torque",
    "Low-Backlash", "Sealed", "Modular", "Rapid-Cycle", "Quiet-Drive",
]

# Fictional customer contacts in the "Ada Lovelace" style: names of deceased
# historical scientists/engineers recombined so no row is a real person.
FIRST_NAMES = [
    "Ada", "Alan", "Grace", "Katherine", "Margaret", "Nikola", "Hedy", "Radia",
    "Annie", "Dorothy", "Claude", "Edsger", "Barbara", "Mary", "Charles",
    "George", "Marie", "Rosalind", "Lise", "Emmy", "Hypatia", "Al-Khwarizmi",
    "Srinivasa", "Chien-Shiung", "Henrietta", "Dennis", "Ken", "Frances",
    "Rear Admiral", "Jean", "Ida", "Philip", "Sophie", "Gottfried", "Blaise",
    "Augusta", "Herman", "Vannevar", "Claude-E", "Jocelyn",
]
LAST_NAMES = [
    "Lovelace-Byron", "Turing-Smith", "Hopper-Jones", "Johnson-Cole", "Hamilton-Reyes",
    "Tesla-Maric", "Lamarr-Kiesler", "Perlman-Aziz", "Easley-Boateng", "Jackson-Proteus",
    "Vaughan-Okoro", "Shannon-Weaver", "Dijkstra-Venn", "Liskov-Wing", "Curie-Sklodowska",
    "Franklin-Gosling", "Meitner-Hahn", "Noether-Frobenius", "Ramanujan-Iyer", "Wu-Chien",
    "Ritchie-Thompson", "Allen-Cocke", "Bartik-Betty", "Holberton-Nash", "Rhodes-Quill",
    "Leibniz-Wolff", "Pascal-Fermat", "Babbage-Ada", "Hollerith-Punch", "Bush-Memex",
]

COMPANY_TOKENS_A = [
    "Quantum", "Apex", "Cobalt", "Vertex", "Pinnacle", "Zephyr", "Halcyon",
    "Meridian", "Ironwood", "Lumen", "Atlas", "Beacon", "Cinder", "Delta",
    "Ember", "Foundry", "Granite", "Helios", "Ion", "Juniper", "Kestrel",
    "Lattice", "Monolith", "Nimbus", "Onyx", "Prairie", "Quarry", "Ridgeline",
    "Summit", "Tundra",
]
COMPANY_TOKENS_B = [
    "Dynamics", "Industries", "Fabrication", "Logistics", "Automation",
    "Manufacturing", "Assembly", "Works", "Systems", "Labs", "Mechatronics",
    "Fulfillment", "Components", "Motion",
]

COUNTRIES = [
    "United States", "Canada", "Mexico", "Brazil", "Germany", "Poland",
    "France", "Spain", "United Kingdom", "Netherlands", "Japan", "South Korea",
    "Singapore", "Australia", "India",
]

ORDER_STATUSES = [
    ("delivered", 0.55), ("shipped", 0.15), ("processing", 0.10),
    ("pending", 0.08), ("cancelled", 0.08), ("refunded", 0.04),
]

REGIONS = [("NA", 0.45), ("EU", 0.30), ("APAC", 0.18), ("LATAM", 0.07)]
CURRENCIES = [("USD", 0.62), ("EUR", 0.24), ("GBP", 0.08), ("JPY", 0.06)]

# metric -> (unit, mean, stddev)
TELEMETRY_METRICS: list[tuple[str, str, float, float]] = [
    ("joint_temperature_c", "celsius", 38.0, 6.0),
    ("battery_pct", "percent", 71.0, 14.0),
    ("torque_nm", "newton_meter", 12.0, 4.0),
    ("vibration_mm_s", "mm_per_second", 2.4, 1.1),
    ("cycle_time_ms", "milliseconds", 850.0, 110.0),
]

# Injected anomaly window (documented in datasets/README.md) for ch18
# observability labs: two robots overheat for one hour.
ANOMALY_START = datetime(2026, 3, 14, 2, 0, 0, tzinfo=timezone.utc)
ANOMALY_END = datetime(2026, 3, 14, 3, 0, 0, tzinfo=timezone.utc)
ANOMALY_ROBOTS = ["R-0142", "R-0207"]

API_PATHS = {
    "v1": [
        ("GET", "/v1/parts", 0.28), ("GET", "/v1/parts/{part_id}", 0.16),
        ("GET", "/v1/orders", 0.20), ("POST", "/v1/orders", 0.10),
        ("GET", "/v1/orders/{order_id}", 0.12), ("GET", "/v1/customers/{customer_id}", 0.08),
        ("GET", "/v1/inventory", 0.06),
    ],
    "v2": [
        ("GET", "/v2/parts", 0.24), ("GET", "/v2/parts/{part_id}", 0.16),
        ("GET", "/v2/orders", 0.18), ("POST", "/v2/orders", 0.12),
        ("GET", "/v2/orders/{order_id}", 0.12), ("GET", "/v2/customers/{customer_id}", 0.08),
        ("GET", "/v2/inventory/levels", 0.06), ("GET", "/v2/telemetry/robots/{robot_id}", 0.04),
    ],
}

# Error bursts for ch14/ch18 labs (documented in datasets/README.md).
BURST_A_START = datetime(2026, 4, 2, 13, 0, 0, tzinfo=timezone.utc)   # 503 storm, v1 orders
BURST_A_END = datetime(2026, 4, 2, 14, 0, 0, tzinfo=timezone.utc)
BURST_B_START = datetime(2026, 5, 20, 9, 15, 0, tzinfo=timezone.utc)   # 500/504, v2 parts
BURST_B_END = datetime(2026, 5, 20, 9, 45, 0, tzinfo=timezone.utc)


def weighted_choice(rng: random.Random, items: list[tuple]) -> object:
    total = sum(w for *_, w in items)
    r = rng.random() * total
    acc = 0.0
    for *vals, w in items:
        acc += w
        if r <= acc:
            return vals[0] if len(vals) == 1 else tuple(vals)
    return items[-1][0] if len(items[-1]) == 2 else items[-1][:-1]


# --------------------------------------------------------------------------- #
# Generators
# --------------------------------------------------------------------------- #

def gen_warehouses() -> bytes:
    rows = [[w, code, name, city, country, cap] for w, code, name, city, country, cap in WAREHOUSES]
    return csv_bytes(["warehouse_id", "code", "name", "city", "country", "capacity_m2"], rows)


def gen_customers(rng: random.Random) -> tuple[bytes, list[str]]:
    rows: list[list[object]] = []
    ids: list[str] = []
    start = datetime(2021, 6, 1, tzinfo=timezone.utc)
    end = datetime(2025, 12, 31, tzinfo=timezone.utc)
    for i in range(1, 2001):
        cid = f"C-{i:04d}"
        ids.append(cid)
        first = rng.choice(FIRST_NAMES).replace(" ", "-")
        last = rng.choice(LAST_NAMES)
        name = f"{first} {last}"
        email = f"{first.lower()}.{last.lower()}.{i:04d}@example.invalid"
        company = f"{rng.choice(COMPANY_TOKENS_A)} {rng.choice(COMPANY_TOKENS_B)}"
        segment = weighted_choice(rng, [("enterprise", 0.18), ("midmarket", 0.37), ("smb", 0.45)])
        country = rng.choice(COUNTRIES)
        created_at = iso(rand_ts(rng, start, end))
        rows.append([cid, name, email, company, segment, country, created_at])
    return csv_bytes(
        ["customer_id", "name", "email", "company", "segment", "country", "created_at"], rows
    ), ids


def gen_parts(rng: random.Random) -> tuple[bytes, bytes, dict[str, tuple[int, str]]]:
    """Returns (parts.csv, parts_sample_100.csv, {part_id: (price_cents, warehouse_id)})."""
    rows: list[list[object]] = []
    meta: dict[str, tuple[int, str]] = {}
    codes = sorted(CATEGORIES)  # fixed order: ACT, CBL, CTL, DRV, EFF, FRM, PWR, SEN
    created_start = datetime(2021, 1, 1, tzinfo=timezone.utc)
    created_end = datetime(2024, 12, 31, tzinfo=timezone.utc)
    for i in range(1, 5001):
        part_id = f"P-{i:05d}"
        code = codes[(i - 1) % len(codes)]
        category, subs, (lo_p, hi_p), (lo_w, hi_w) = CATEGORIES[code]
        sub = subs[((i - 1) // len(codes)) % len(subs)]
        adjective = PART_ADJECTIVES[(i * 7) % len(PART_ADJECTIVES)]
        model = f"{chr(65 + (i % 26))}{chr(65 + ((i * 13) % 26))}-{100 + (i * 37) % 900}"
        name = f"{adjective} {sub} {model}"
        sku = f"NR-{code}-{i:05d}"
        # keep price inside category band while staying varied
        price = max(lo_p, min(hi_p, int((lo_p + hi_p) / 2 + rng.gauss(0, (hi_p - lo_p) / 4))))
        weight = max(lo_w, min(hi_w, int((lo_w + hi_w) / 2 + rng.gauss(0, (hi_w - lo_w) / 4))))
        warehouse = WAREHOUSES[(i * 3 + rng.randrange(8)) % len(WAREHOUSES)][0]
        active = "true" if rng.random() < 0.95 else "false"
        created_at = rand_ts(rng, created_start, created_end)
        updated_at = created_at + timedelta(seconds=rng.randrange(0, 400 * 86400))
        rows.append([
            part_id, sku, name, category, sub, price, weight, warehouse,
            active, iso(created_at), iso(updated_at),
        ])
        meta[part_id] = (price, warehouse)
    header = ["part_id", "sku", "name", "category", "subcategory",
              "unit_price_cents", "weight_grams", "warehouse_id", "active",
              "created_at", "updated_at"]
    full = csv_bytes(header, rows)
    sample = csv_bytes(header, rows[:100])
    return full, sample, meta


def gen_orders(
    rng: random.Random,
    customer_ids: list[str],
    parts_meta: dict[str, tuple[int, str]],
) -> tuple[bytes, bytes]:
    part_ids = sorted(parts_meta)
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 6, 30, 23, 59, 59, tzinfo=timezone.utc)
    order_rows: list[list[object]] = []
    line_rows: list[list[object]] = []
    for i in range(1, 20001):
        order_id = f"O-{100000 + i}"
        customer_id = rng.choice(customer_ids)
        status = weighted_choice(rng, ORDER_STATUSES)
        ts = rand_ts(rng, start, end)
        currency = weighted_choice(rng, CURRENCIES)
        region = weighted_choice(rng, REGIONS)
        n_lines = rng.randint(1, 5)
        total = 0
        chosen = rng.sample(part_ids, n_lines)
        for line_no, pid in enumerate(chosen, start=1):
            qty = rng.randint(1, 25)
            price = parts_meta[pid][0]
            line_rows.append([order_id, line_no, pid, qty, price])
            total += qty * price
        order_rows.append([order_id, customer_id, status, iso(ts), total, currency, region])
    orders_csv = csv_bytes(
        ["order_id", "customer_id", "status", "order_ts", "total_cents", "currency", "region"],
        order_rows,
    )
    lines_csv = csv_bytes(
        ["order_id", "line_no", "part_id", "qty", "unit_price_cents"], line_rows
    )
    return orders_csv, lines_csv


def gen_inventory(
    rng: random.Random, parts_meta: dict[str, tuple[int, str]]
) -> bytes:
    wh_ids = [w[0] for w in WAREHOUSES]
    start = datetime(2026, 6, 1, tzinfo=timezone.utc)
    end = datetime(2026, 6, 30, 23, 59, 59, tzinfo=timezone.utc)
    rows: list[list[object]] = []
    for part_id in sorted(parts_meta):
        home = parts_meta[part_id][1]
        extras = rng.sample([w for w in wh_ids if w != home], rng.randint(0, 2))
        for wh in [home, *extras]:
            on_hand = rng.randint(0, 2000)
            reserved = rng.randint(0, on_hand // 4)
            reorder_point = rng.randint(50, 300)
            updated = iso(rand_ts(rng, start, end))
            rows.append([wh, part_id, on_hand, reserved, reorder_point, updated])
    return csv_bytes(
        ["warehouse_id", "part_id", "on_hand", "reserved", "reorder_point", "updated_at"], rows
    )


def gen_telemetry(rng: random.Random) -> bytes:
    start = datetime(2026, 3, 1, tzinfo=timezone.utc)
    end = datetime(2026, 3, 31, 23, 59, 59, tzinfo=timezone.utc)
    n_total = 50000
    n_anomaly = 500
    records: list[dict] = []
    for _ in range(n_total - n_anomaly):
        robot = f"R-{rng.randint(1, 300):04d}"
        metric, unit, mean, sd = TELEMETRY_METRICS[rng.randrange(len(TELEMETRY_METRICS))]
        value = round(rng.gauss(mean, sd), 2)
        if metric == "battery_pct":
            value = max(0.0, min(100.0, value))
        records.append({
            "event_id": "",  # assigned after sorting
            "robot_id": robot,
            "ts": iso(rand_ts(rng, start, end)),
            "metric": metric,
            "value": value,
            "unit": unit,
        })
    for _ in range(n_anomaly):
        robot = rng.choice(ANOMALY_ROBOTS)
        records.append({
            "event_id": "",
            "robot_id": robot,
            "ts": iso(rand_ts(rng, ANOMALY_START, ANOMALY_END)),
            "metric": "joint_temperature_c",
            "value": round(rng.gauss(96.0, 4.5), 2),
            "unit": "celsius",
        })
    records.sort(key=lambda r: r["ts"])
    for idx, rec in enumerate(records, start=1):
        rec["event_id"] = f"te-{idx:07d}"
        # keep event_id first in key order for readable diffs
        rec_move = {"event_id": rec.pop("event_id")}
        rec_move.update(rec)
        records[idx - 1] = rec_move
    return jsonl_bytes(records)


def gen_api_access_log(rng: random.Random) -> bytes:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 6, 30, 23, 59, 59, tzinfo=timezone.utc)
    span = (end - start).total_seconds()
    n_normal = 27000
    n_burst_a = 1800
    n_burst_b = 1200
    consumers = [f"cons-{i:03d}" for i in range(1, 41)]
    normal_statuses = [(200, 0.88), (201, 0.03), (400, 0.03), (401, 0.015),
                       (404, 0.03), (429, 0.015)]

    records: list[dict] = []

    def pick_version(ts: datetime) -> str:
        # Visible v1 -> v2 migration trend: v1 traffic share declines linearly
        # from 80% in January 2026 to 10% by end of June 2026.
        progress = (ts - start).total_seconds() / span
        p_v1 = 0.80 - 0.70 * progress
        return "v1" if rng.random() < p_v1 else "v2"

    for _ in range(n_normal):
        ts = rand_ts(rng, start, end)
        version = pick_version(ts)
        method, path = weighted_choice(rng, API_PATHS[version])[:2]
        status = weighted_choice(rng, normal_statuses)
        if method == "GET" and status == 201:
            status = 200
        base_mu = 3.4 if version == "v1" else 3.0  # v2 is faster
        latency = max(2, int(rng.lognormvariate(base_mu, 0.7)))
        if status >= 500:
            latency *= 8
        records.append({
            "ts": iso(ts), "request_id": "", "consumer_id": rng.choice(consumers),
            "api_version": version, "method": method, "path": path,
            "status": status, "latency_ms": latency,
        })

    for _ in range(n_burst_a):  # 503 storm on POST /v1/orders
        ts = rand_ts(rng, BURST_A_START, BURST_A_END)
        status = 503 if rng.random() < 0.85 else 500
        records.append({
            "ts": iso(ts), "request_id": "", "consumer_id": rng.choice(consumers),
            "api_version": "v1", "method": "POST", "path": "/v1/orders",
            "status": status, "latency_ms": rng.randint(5000, 30000),
        })

    for _ in range(n_burst_b):  # 500/504 on GET /v2/parts
        ts = rand_ts(rng, BURST_B_START, BURST_B_END)
        status = 500 if rng.random() < 0.80 else 504
        records.append({
            "ts": iso(ts), "request_id": "", "consumer_id": rng.choice(consumers),
            "api_version": "v2", "method": "GET", "path": "/v2/parts",
            "status": status, "latency_ms": rng.randint(8000, 25000),
        })

    records.sort(key=lambda r: r["ts"])
    for idx, rec in enumerate(records, start=1):
        rid = hashlib.sha256(f"northwind-api-log-{idx}".encode()).hexdigest()[:16]
        ordered = {
            "ts": rec["ts"], "request_id": f"req-{rid}",
            "consumer_id": rec["consumer_id"], "api_version": rec["api_version"],
            "method": rec["method"], "path": rec["path"],
            "status": rec["status"], "latency_ms": rec["latency_ms"],
        }
        records[idx - 1] = ordered
    return jsonl_bytes(records)


# --------------------------------------------------------------------------- #
# Webhook fixtures (chapter 11 scheme: HMAC-SHA256 over "<timestamp>.<body>",
# signature header "t=<ts>,v1=<hex>")
# --------------------------------------------------------------------------- #

def webhook_fixture(name: str, description: str, ts: int, body_obj: dict,
                    tamper: bool = False) -> bytes:
    body = json.dumps(body_obj, separators=(",", ":"))
    msg = f"{ts}.{body}".encode("utf-8")
    sig = hmac.new(WEBHOOK_SIGNING_KEY, msg, hashlib.sha256).hexdigest()
    if tamper:
        sig = ("0" if sig[0] != "0" else "1") + sig[1:]
    fixture = {
        "name": name,
        "description": description,
        "scheme": "HMAC-SHA256 over '<timestamp>.<body>'; header X-Northwind-Signature: t=<ts>,v1=<hex>",
        "signing_key_file": "TEST-ONLY_signing_key.txt",
        "timestamp": ts,
        "headers": {
            "Content-Type": "application/json",
            "X-Northwind-Signature": f"t={ts},v1={sig}",
        },
        "body": body,
        "expected_verification": "fail" if tamper else "pass",
    }
    return (json.dumps(fixture, indent=2) + "\n").encode("utf-8")


def gen_webhooks() -> dict[str, bytes]:
    key_note = (
        "TEST-ONLY SIGNING KEY - NOT A REAL SECRET\n"
        "=========================================\n"
        "This key is part of the synthetic Northwind Robotics teaching dataset for\n"
        "'Mastering APIs: From Zero to Production Guru' (chapter 11). It exists only\n"
        "so webhook-signature verification labs are reproducible offline.\n"
        "Never use it in any real system.\n\n"
        f"key: {WEBHOOK_SIGNING_KEY.decode()}\n"
    )
    files = {
        "webhooks/TEST-ONLY_signing_key.txt": txt_bytes(key_note),
        "webhooks/README.md": txt_bytes(WEBHOOKS_README),
        "webhooks/orders_created.json": webhook_fixture(
            "orders.created",
            "A new order was placed (valid signature).",
            1772064000,  # 2026-02-26T00:00:00Z
            {
                "id": "evt_01JNRWT0001SYNTHETIC000001",
                "type": "orders.created",
                "created": "2026-02-26T00:00:00Z",
                "data": {
                    "order_id": "O-100042",
                    "customer_id": "C-0017",
                    "status": "pending",
                    "total_cents": 184500,
                    "currency": "USD",
                    "region": "NA",
                },
            },
        ),
        "webhooks/orders_fulfilled.json": webhook_fixture(
            "orders.fulfilled",
            "An order was fulfilled at a warehouse (valid signature).",
            1772323200,  # 2026-03-01T00:00:00Z
            {
                "id": "evt_01JNRWT0002SYNTHETIC000002",
                "type": "orders.fulfilled",
                "created": "2026-03-01T00:00:00Z",
                "data": {
                    "order_id": "O-100017",
                    "warehouse_id": "W-01",
                    "shipped_lines": 3,
                    "carrier": "Northwind Freight (fictional)",
                },
            },
        ),
        "webhooks/inventory_low_stock.json": webhook_fixture(
            "inventory.low_stock",
            "Stock dropped below the reorder point (valid signature).",
            1772496000,  # 2026-03-03T00:00:00Z
            {
                "id": "evt_01JNRWT0003SYNTHETIC000003",
                "type": "inventory.low_stock",
                "created": "2026-03-03T00:00:00Z",
                "data": {
                    "part_id": "P-00142",
                    "warehouse_id": "W-04",
                    "on_hand": 37,
                    "reorder_point": 120,
                },
            },
        ),
        "webhooks/bad_signature.json": webhook_fixture(
            "orders.created (tampered)",
            "Negative test: signature was tampered with; verification MUST fail.",
            1772064000,
            {
                "id": "evt_01JNRWT0004SYNTHETIC000004",
                "type": "orders.created",
                "created": "2026-02-26T00:00:00Z",
                "data": {
                    "order_id": "O-100099",
                    "customer_id": "C-0003",
                    "status": "pending",
                    "total_cents": 9900,
                    "currency": "USD",
                    "region": "EU",
                },
            },
            tamper=True,
        ),
    }
    return files


WEBHOOKS_README = """# Webhook fixtures (chapter 11)

Synthetic signed-webhook payloads implementing the book's chapter 11 scheme:

* Signature: `HMAC-SHA256(key, "<timestamp>.<body>")`, hex-encoded.
* Header: `X-Northwind-Signature: t=<unix_ts>,v1=<hex>`.
* Receivers must reject timestamps older than 5 minutes (replay protection).

## Files

| File | Event | Expected verification |
|---|---|---|
| `orders_created.json` | `orders.created` | pass |
| `orders_fulfilled.json` | `orders.fulfilled` | pass |
| `inventory_low_stock.json` | `inventory.low_stock` | pass |
| `bad_signature.json` | `orders.created` (tampered) | **fail** |
| `TEST-ONLY_signing_key.txt` | shared test key | n/a |

Each fixture is JSON with `headers` and the exact raw `body` string. Verify with:

```powershell
# PowerShell-friendly Python one-liner style; see chapter 11 labs for full code
python -c "import hmac,hashlib,json; f=json.load(open(r'datasets\\northwind_robotics\\webhooks\\orders_created.json')); k=open(r'datasets\\northwind_robotics\\webhooks\\TEST-ONLY_signing_key.txt').read().split('key: ')[1].strip().encode(); t=f['timestamp']; sig=hmac.new(k, f'{t}.{f[\"body\"]}'.encode(), hashlib.sha256).hexdigest(); print('pass' if f't={t},v1={sig}' == f['headers']['X-Northwind-Signature'] else 'fail')"
```

All keys, IDs, and payloads are synthetic and safe to commit.
"""


# --------------------------------------------------------------------------- #
# OpenAPI 3.1 specs (chapter 20 governance labs)
# --------------------------------------------------------------------------- #

OPENAPI_PARTS = """# Northwind Robotics Parts API v2 -- compliant reference spec (ch20 style rules)
openapi: 3.1.0
info:
  title: Northwind Robotics Parts API
  version: 2.4.0
  description: Read access to the Northwind Robotics synthetic parts catalog.
  contact:
    name: Northwind Robotics API Platform (fictional)
    email: api-platform@example.invalid
  license:
    name: Proprietary (synthetic teaching material)
servers:
  - url: https://api.northwind-robotics.example.invalid/v2
    description: Production (synthetic)
tags:
  - name: parts
    description: Operations on the parts catalog.
paths:
  /parts:
    get:
      operationId: listParts
      summary: List parts
      description: Returns a paginated list of catalog parts with optional filters.
      tags: [parts]
      parameters:
        - name: category
          in: query
          description: Filter by top-level category.
          schema:
            type: string
        - name: active
          in: query
          description: Filter by lifecycle state.
          schema:
            type: boolean
        - name: cursor
          in: query
          description: Opaque pagination cursor from a previous response.
          schema:
            type: string
        - name: limit
          in: query
          description: Maximum items per page (default 50, max 200).
          schema:
            type: integer
            minimum: 1
            maximum: 200
            default: 50
      responses:
        "200":
          description: A page of parts.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/PartPage"
        "400":
          description: Invalid query parameters.
          content:
            application/problem+json:
              schema:
                $ref: "#/components/schemas/Problem"
        "429":
          description: Rate limit exceeded.
          content:
            application/problem+json:
              schema:
                $ref: "#/components/schemas/Problem"
  /parts/{part_id}:
    get:
      operationId: getPart
      summary: Get one part
      description: Returns a single part by identifier.
      tags: [parts]
      parameters:
        - name: part_id
          in: path
          required: true
          description: Part identifier (e.g. P-00142).
          schema:
            type: string
            pattern: '^P-\\d{5}$'
      responses:
        "200":
          description: The requested part.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Part"
        "404":
          description: Part not found.
          content:
            application/problem+json:
              schema:
                $ref: "#/components/schemas/Problem"
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  schemas:
    Part:
      type: object
      required: [part_id, sku, name, category, unit_price_cents, active]
      properties:
        part_id:
          type: string
        sku:
          type: string
        name:
          type: string
        category:
          type: string
        subcategory:
          type: string
        unit_price_cents:
          type: integer
          minimum: 0
        weight_grams:
          type: integer
          minimum: 0
        warehouse_id:
          type: string
        active:
          type: boolean
    PartPage:
      type: object
      required: [items, next_cursor]
      properties:
        items:
          type: array
          items:
            $ref: "#/components/schemas/Part"
        next_cursor:
          type: string
          nullable: true
    Problem:
      type: object
      required: [type, title, status]
      properties:
        type:
          type: string
          format: uri
        title:
          type: string
        status:
          type: integer
        detail:
          type: string
        instance:
          type: string
security:
  - bearerAuth: []
"""

OPENAPI_ORDERS = """# Northwind Robotics Orders API v2 -- compliant reference spec (ch20 style rules)
openapi: 3.1.0
info:
  title: Northwind Robotics Orders API
  version: 2.1.0
  description: Order placement and tracking for the synthetic Northwind Robotics universe.
  contact:
    name: Northwind Robotics API Platform (fictional)
    email: api-platform@example.invalid
  license:
    name: Proprietary (synthetic teaching material)
servers:
  - url: https://api.northwind-robotics.example.invalid/v2
    description: Production (synthetic)
tags:
  - name: orders
    description: Create and track orders.
paths:
  /orders:
    post:
      operationId: createOrder
      summary: Create an order
      description: Creates an order. Idempotent via the Idempotency-Key header (ch10).
      tags: [orders]
      parameters:
        - name: Idempotency-Key
          in: header
          required: true
          description: Client-supplied idempotency key for safe retries.
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/OrderCreate"
      responses:
        "201":
          description: Order created.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Order"
        "400":
          description: Validation failure.
          content:
            application/problem+json:
              schema:
                $ref: "#/components/schemas/Problem"
        "409":
          description: Idempotency-key conflict with a different payload.
          content:
            application/problem+json:
              schema:
                $ref: "#/components/schemas/Problem"
    get:
      operationId: listOrders
      summary: List orders
      description: Returns a paginated list of orders, newest first.
      tags: [orders]
      parameters:
        - name: customer_id
          in: query
          description: Filter by customer.
          schema:
            type: string
        - name: status
          in: query
          description: Filter by lifecycle status.
          schema:
            type: string
            enum: [pending, processing, shipped, delivered, cancelled, refunded]
        - name: cursor
          in: query
          description: Opaque pagination cursor.
          schema:
            type: string
        - name: limit
          in: query
          description: Page size (default 50, max 200).
          schema:
            type: integer
            minimum: 1
            maximum: 200
            default: 50
      responses:
        "200":
          description: A page of orders.
          content:
            application/json:
              schema:
                type: object
                required: [items, next_cursor]
                properties:
                  items:
                    type: array
                    items:
                      $ref: "#/components/schemas/Order"
                  next_cursor:
                    type: string
                    nullable: true
        "429":
          description: Rate limit exceeded.
          content:
            application/problem+json:
              schema:
                $ref: "#/components/schemas/Problem"
  /orders/{order_id}:
    get:
      operationId: getOrder
      summary: Get one order
      description: Returns a single order including its line items.
      tags: [orders]
      parameters:
        - name: order_id
          in: path
          required: true
          description: Order identifier (e.g. O-100042).
          schema:
            type: string
            pattern: '^O-\\d{6}$'
      responses:
        "200":
          description: The requested order.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Order"
        "404":
          description: Order not found.
          content:
            application/problem+json:
              schema:
                $ref: "#/components/schemas/Problem"
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  schemas:
    OrderLine:
      type: object
      required: [line_no, part_id, qty, unit_price_cents]
      properties:
        line_no:
          type: integer
          minimum: 1
        part_id:
          type: string
        qty:
          type: integer
          minimum: 1
        unit_price_cents:
          type: integer
          minimum: 0
    OrderCreate:
      type: object
      required: [customer_id, currency, lines]
      properties:
        customer_id:
          type: string
        currency:
          type: string
          enum: [USD, EUR, GBP, JPY]
        lines:
          type: array
          minItems: 1
          items:
            $ref: "#/components/schemas/OrderLine"
    Order:
      type: object
      required: [order_id, customer_id, status, order_ts, total_cents, currency, region, lines]
      properties:
        order_id:
          type: string
        customer_id:
          type: string
        status:
          type: string
          enum: [pending, processing, shipped, delivered, cancelled, refunded]
        order_ts:
          type: string
          format: date-time
        total_cents:
          type: integer
          minimum: 0
        currency:
          type: string
        region:
          type: string
          enum: [NA, EU, APAC, LATAM]
        lines:
          type: array
          items:
            $ref: "#/components/schemas/OrderLine"
    Problem:
      type: object
      required: [type, title, status]
      properties:
        type:
          type: string
          format: uri
        title:
          type: string
        status:
          type: integer
        detail:
          type: string
        instance:
          type: string
security:
  - bearerAuth: []
"""

# INTENTIONALLY NON-COMPLIANT: used by ch20 linter labs. Violations are
# catalogued in datasets/README.md and in the header comment below.
OPENAPI_LEGACY_INVENTORY = """# Northwind Robotics Legacy Inventory API v1
# !!! INTENTIONALLY NON-COMPLIANT - ch20 linter-lab fixture !!!
# Deliberate violations of the book's chapter 20 style rules:
#   1. No operationId on any operation.
#   2. No info.contact and no info.license.
#   3. Operations lack descriptions (only terse summaries).
#   4. Error responses (4xx/5xx) missing on every operation.
#   5. No application/problem+json error model at all.
#   6. Inconsistent naming: camelCase path params and properties mixed with
#      snake_case; path segment uses Capitalized_Snake case.
#   7. No pagination contract on the collection endpoint (no cursor/limit).
#   8. Tags used but never declared/described.
#   9. No security scheme declared.
#  10. Version string is not semver ('v1').
openapi: 3.1.0
info:
  title: Legacy Inventory API
  version: v1
paths:
  /Inventory_Items:
    get:
      summary: get inventory
      tags: [inventory]
      responses:
        "200":
          description: ok
          content:
            application/json:
              schema:
                type: object
                properties:
                  Items:
                    type: array
                    items:
                      $ref: "#/components/schemas/InventoryItem"
  /Inventory_Items/{partId}:
    put:
      summary: update stock
      tags: [inventory]
      parameters:
        - name: partId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/StockUpdate"
      responses:
        "200":
          description: ok
components:
  schemas:
    InventoryItem:
      type: object
      properties:
        PartID:
          type: string
        warehouse_id:
          type: string
        OnHand:
          type: integer
        reorderPoint:
          type: integer
    StockUpdate:
      type: object
      properties:
        on_hand:
          type: integer
        Reason:
          type: string
"""


# --------------------------------------------------------------------------- #
# Build orchestration
# --------------------------------------------------------------------------- #

def build_all() -> dict[str, bytes]:
    """Regenerate every dataset. Keys are paths relative to OUT_DIR."""
    rng = random.Random(SEED)
    files: dict[str, bytes] = {}

    files["warehouses.csv"] = gen_warehouses()

    customers_csv, customer_ids = gen_customers(rng)
    files["customers.csv"] = customers_csv

    parts_csv, parts_sample, parts_meta = gen_parts(rng)
    files["parts.csv"] = parts_csv
    files["parts_sample_100.csv"] = parts_sample

    orders_csv, lines_csv = gen_orders(rng, customer_ids, parts_meta)
    files["orders.csv"] = orders_csv
    files["order_lines.csv"] = lines_csv

    files["inventory.csv"] = gen_inventory(rng, parts_meta)
    files["telemetry_events.jsonl"] = gen_telemetry(rng)
    files["api_access_log.jsonl"] = gen_api_access_log(rng)

    files["openapi/parts-api.yaml"] = txt_bytes(OPENAPI_PARTS)
    files["openapi/orders-api.yaml"] = txt_bytes(OPENAPI_ORDERS)
    files["openapi/legacy-inventory-api.yaml"] = txt_bytes(OPENAPI_LEGACY_INVENTORY)

    files.update(gen_webhooks())
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify on-disk files match regeneration; exit 1 on any drift",
    )
    args = parser.parse_args()

    files = build_all()

    if args.check:
        failures = 0
        for rel, data in sorted(files.items()):
            path = OUT_DIR / rel
            if not path.exists():
                print(f"MISSING  {rel}")
                failures += 1
            elif path.read_bytes() != data:
                print(f"DRIFTED  {rel}")
                failures += 1
        if failures:
            print(f"--check FAILED: {failures} file(s) missing or drifted")
            return 1
        print(f"--check OK: {len(files)} files match regeneration (seed={SEED})")
        return 0

    for rel, data in sorted(files.items()):
        path = OUT_DIR / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        print(f"wrote {rel} ({len(data):,} bytes)")
    print(f"done: {len(files)} files regenerated deterministically (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
