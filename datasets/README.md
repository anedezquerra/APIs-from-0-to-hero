# Datasets — "Mastering APIs: From Zero to Production Guru"

Synthetic, deterministic, offline datasets for the fictional **Northwind Robotics**
universe (industrial robotics company: parts catalog, orders, inventory, warehouses,
robot-fleet telemetry, customers, API consumers). Used by labs and the 110 capstone
projects throughout the book.

Everything here is **synthetic**: fictional people (names are recombinations of
deceased historical figures, e.g. "Ada Lovelace-Byron"), emails on
`example.invalid`, a test-only webhook signing key. **No real PII, no secrets.**

## Quick start (PowerShell)

```powershell
# Regenerate every dataset (byte-for-byte deterministic, seed = 42)
python .\datasets\generate_all.py

# CI check: exit 0 iff committed files match regeneration
python .\datasets\generate_all.py --check
```

Generator constraints: Python 3.11+, **standard library only**, no network.
All files are UTF-8 with `\n` newlines; timestamps are ISO-8601 UTC (`...Z`).

## Dataset inventory

| File | Format | Rows | Size (approx.) | Primary consumers |
|---|---|---|---|---|
| `northwind_robotics\warehouses.csv` | CSV | 8 | 0.5 KB | ch6, ch8; capstones with inventory |
| `northwind_robotics\parts.csv` | CSV | 5,000 | 732 KB | ch2, ch4, ch8, ch9, ch20 |
| `northwind_robotics\parts_sample_100.csv` | CSV | 100 | 15 KB | ch2 quick labs (first 100 rows of `parts.csv`) |
| `northwind_robotics\customers.csv` | CSV | 2,000 | 252 KB | ch2, ch4, ch16 |
| `northwind_robotics\orders.csv` | CSV | 20,000 | 1.2 MB | ch6–ch10, ch12–ch13 |
| `northwind_robotics\order_lines.csv` | CSV | 60,071 | 1.7 MB | ch8, ch10, ch12 |
| `northwind_robotics\inventory.csv` | CSV | 10,034 | 458 KB | ch6, ch8, ch13 |
| `northwind_robotics\telemetry_events.jsonl` | NDJSON | 50,000 | 6.7 MB | ch18 (observability), ch11 (streams) |
| `northwind_robotics\api_access_log.jsonl` | NDJSON | 30,000 | 5.4 MB | ch9 (versioning), ch14 (rate limiting), ch18, ch20 |
| `northwind_robotics\openapi\parts-api.yaml` | OpenAPI 3.1 | — | 4 KB | ch6, ch19, ch20 (compliant reference) |
| `northwind_robotics\openapi\orders-api.yaml` | OpenAPI 3.1 | — | 6 KB | ch6, ch10, ch19, ch20 (compliant reference) |
| `northwind_robotics\openapi\legacy-inventory-api.yaml` | OpenAPI 3.1 | — | 2 KB | ch20 linter labs (**intentionally non-compliant**) |
| `northwind_robotics\webhooks\*.json` | JSON fixtures | 4 | <1 KB each | ch11 (signed webhooks) |
| `northwind_robotics\webhooks\TEST-ONLY_signing_key.txt` | text | — | 0.4 KB | ch11 labs (test-only key) |

## Schemas

### `warehouses.csv`
`warehouse_id` (W-01…W-08), `code`, `name`, `city`, `country`, `capacity_m2`.

### `parts.csv`
| Column | Type | Notes |
|---|---|---|
| `part_id` | string | `P-00001`…`P-05000`, primary key |
| `sku` | string | `NR-<CAT>-<seq>`, unique |
| `name` | string | e.g. `Precision Servo Motor KX-214` |
| `category` | string | one of 8 categories (Actuators, Sensors, Controllers, Power Systems, Frames and Structure, End Effectors, Drivetrain, Cabling and Connectors) |
| `subcategory` | string | category-dependent |
| `unit_price_cents` | int | positive; `order_lines.unit_price_cents` matches this |
| `weight_grams` | int | positive |
| `warehouse_id` | string | home warehouse, FK → `warehouses.warehouse_id` |
| `active` | bool (`true`/`false`) | ~5% inactive |
| `created_at`, `updated_at` | ISO-8601 UTC | `updated_at >= created_at` |

`parts_sample_100.csv` is the header plus the first 100 data rows of `parts.csv`
(same schema) for quick labs that should not scan 5,000 rows.

### `customers.csv`
`customer_id` (C-0001…C-2000, PK), `name` (fictional recombined historical
names), `email` (`*.####@example.invalid`, unique), `company` (fictional),
`segment` (`enterprise`/`midmarket`/`smb`), `country`, `created_at`.

### `orders.csv`
`order_id` (O-100001…O-120000, PK), `customer_id` (FK → `customers`),
`status` (`pending`/`processing`/`shipped`/`delivered`/`cancelled`/`refunded`),
`order_ts` (ISO-8601 UTC, 2025-01-01…2026-06-30), `total_cents`
(**always equals** `Σ qty × unit_price_cents` over its `order_lines`),
`currency` (`USD`/`EUR`/`GBP`/`JPY`), `region` (`NA`/`EU`/`APAC`/`LATAM`).

### `order_lines.csv`
`order_id` (FK → `orders`), `line_no` (1..n per order, composite PK with
`order_id`), `part_id` (FK → `parts`), `qty` (1–25), `unit_price_cents`
(matches `parts.unit_price_cents`).

### `inventory.csv`
`warehouse_id` (FK → `warehouses`), `part_id` (FK → `parts`), `on_hand`,
`reserved` (`≤ on_hand/4`), `reorder_point`, `updated_at`. Each part is stocked
in its home warehouse plus 0–2 additional warehouses.

### `telemetry_events.jsonl`
One JSON object per line: `event_id` (`te-0000001`…, assigned after sorting by
`ts`), `robot_id` (`R-0001`…`R-0300`), `ts` (ISO-8601 UTC,
2026-03-01…2026-03-31), `metric`, `value`, `unit`.

Metrics: `joint_temperature_c` (celsius), `battery_pct` (percent),
`torque_nm` (newton_meter), `vibration_mm_s` (mm_per_second),
`cycle_time_ms` (milliseconds).

**Injected anomaly window (for ch18 observability labs):**
`2026-03-14T02:00:00Z`–`2026-03-14T03:00:00Z` — robots **R-0142** and **R-0207**
report `joint_temperature_c` ≈ 96 °C (≈ 500 events, normal fleet mean is 38 °C).
Labs: detect the window with rolling statistics, then alert on it.

### `api_access_log.jsonl`
One JSON object per line: `ts` (ISO-8601 UTC, 2026-01-01…2026-06-30),
`request_id` (`req-<16 hex>`), `consumer_id` (`cons-001`…`cons-040`),
`api_version` (`v1`/`v2`), `method`, `path`, `status`, `latency_ms`.

Deliberate features (for ch9/ch14/ch18/ch20 labs):

* **v1 → v2 migration trend:** v1 traffic share declines roughly linearly from
  ~75% in January to ~15% by end of June 2026. v2 latencies are lower than v1.
* **Error burst A:** `2026-04-02T13:00–14:00Z` — 503/500 storm on
  `POST /v1/orders` (~1,800 events, latency 5–30 s). Because burst A is v1-only,
  April's v1 share blips upward — a useful discussion point.
* **Error burst B:** `2026-05-20T09:15–09:45Z` — 500/504 spike on
  `GET /v2/parts` (~1,200 events, latency 8–25 s).
* Background 429s (~1.5%) for rate-limiting labs; 400/401/404 at low rates.

### `openapi/` (OpenAPI 3.1 specs)

| Spec | Status | Purpose |
|---|---|---|
| `parts-api.yaml` | compliant | Reference spec for the Parts API v2 (cursor pagination, RFC 9457 `application/problem+json` errors, `operationId`s, documented tags, bearer auth) |
| `orders-api.yaml` | compliant | Reference spec for the Orders API v2 (adds `Idempotency-Key` header + 409 semantics for ch10) |
| `legacy-inventory-api.yaml` | **intentionally non-compliant** | ch20 linter-lab fixture. Deliberate violations (also listed in the file header): 1) no `operationId`s, 2) no `info.contact`/`info.license`, 3) operations without descriptions, 4) no 4xx/5xx responses, 5) no `application/problem+json` model, 6) mixed camelCase/PascalCase/snake_case naming + `Capitalized_Snake` path, 7) collection endpoint with no pagination contract, 8) undeclared tags, 9) no security scheme, 10) non-semver version string. All three specs are valid YAML and parse as OpenAPI 3.1 documents. |

### `webhooks/` (chapter 11 signed-webhook fixtures)

Scheme: `v1 = hex(HMAC-SHA256(key, "<unix_timestamp>.<raw_body>"))`, sent as
header `X-Northwind-Signature: t=<ts>,v1=<hex>`. Receivers should also enforce a
5-minute timestamp tolerance (replay protection).

| Fixture | Event | Expected verification |
|---|---|---|
| `orders_created.json` | `orders.created` | pass |
| `orders_fulfilled.json` | `orders.fulfilled` | pass |
| `inventory_low_stock.json` | `inventory.low_stock` | pass |
| `bad_signature.json` | tampered signature | **fail** (negative test) |

The shared HMAC key lives in `TEST-ONLY_signing_key.txt` and is clearly marked
as a **synthetic test-only secret** so verification labs are reproducible
offline. See `webhooks\README.md` for the verification one-liner.

## Consistency guarantees (verified by labs and CI)

* `order_lines.part_id ⊆ parts.part_id`, `orders.customer_id ⊆ customers.customer_id`,
  `inventory.part_id ⊆ parts.part_id`, `inventory.warehouse_id ⊆ warehouses.warehouse_id`,
  `parts.warehouse_id ⊆ warehouses.warehouse_id`.
* `orders.total_cents == Σ qty × unit_price_cents` of its lines; line prices
  equal the catalog price.
* All timestamps ISO-8601 UTC; all files UTF-8 with `\n` newlines.
* `python .\datasets\generate_all.py --check` exits 0 (byte-stable regeneration
  on Windows).

## Chapter / capstone consumption map

* **ch2** consuming APIs: `parts_sample_100.csv`, `customers.csv`
* **ch4** serialization/contracts: `parts.csv`, `customers.csv`
* **ch6** building APIs (FastAPI): `parts.csv`, `orders.csv`, `inventory.csv`, `openapi\*.yaml`
* **ch8** pagination/filtering/sorting: `parts.csv`, `orders.csv`, `order_lines.csv`
* **ch9** versioning/evolution: `api_access_log.jsonl` (v1→v2 trend)
* **ch10** idempotency: `orders.csv`, `openapi\orders-api.yaml`
* **ch11** async/event-driven: `webhooks\*`, `telemetry_events.jsonl`
* **ch12** GraphQL / **ch13** gRPC: `orders.csv` + `order_lines.csv` join workloads
* **ch14** rate limiting: `api_access_log.jsonl` (429s, bursts)
* **ch16** API security: `customers.csv` (obviously-fake PII handling), webhook signatures
* **ch18** observability/SRE: `telemetry_events.jsonl` (anomaly window), `api_access_log.jsonl` (error bursts, latency)
* **ch19** testing: all fixtures as golden files
* **ch20** lifecycle/governance/DX: `openapi\*` (linter labs), `api_access_log.jsonl` (deprecation analytics)
* **Capstones** (01–110): combinations of the above per capstone brief.
