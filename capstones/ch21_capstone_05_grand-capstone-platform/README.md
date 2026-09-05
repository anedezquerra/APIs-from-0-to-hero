# Capstone 21.5 — The Grand Capstone: Northwind Robotics API Platform [staff]

> Build the complete platform of the chapter's Grand Capstone specification: all five API surfaces, the four milestones, and the acceptance rubric — as a coherent, governed, observable system.

## Objective

Build the Northwind Robotics API Platform as a set of deployable services
plus the governance toolchain that keeps them honest. Four domains:
**catalog** (products, categories, pricing), **orders** (placement, status,
partner notification), **inventory** (stock reservation, restock), and
**telemetry** (fleet readings, operator dashboards). Synthetic data only;
all services run offline on one machine with in-process fakes for the
broker, payments, and identity provider.

## Layout

```
services\    # one module per domain service (catalog, orders, inventory, telemetry)
specs\       # contract artifacts: OpenAPI, GraphQL SDL, .proto, AsyncAPI
tests\       # milestone acceptance tests (in-process, offline)
starter.py   # milestone runner CLI
```

## API Surfaces (each cites its governing spec artifact)

| Surface | Profile | Contract |
|---------|---------|----------|
| `/v1/products`, `/v1/orders` | REST + OpenAPI | keyset pagination, date version, RFC 9457 errors, idempotency keys |
| `/graphql` | GraphQL | read model over catalog + telemetry; depth ≤ 5; persisted queries |
| `inventory.v1.Inventory` | gRPC | `Reserve`/`Release`/`WatchStock` (server stream) |
| `order.created`, `order.shipped` | webhooks | signed (HMAC), delivery log, replay endpoint, AsyncAPI spec |
| `/v1/telemetry/stream` | SSE | operator dashboard feed, `Last-Event-ID` resume |

## Non-Functional Requirements (condensed)

- **SLOs:** catalog read p99 < 200 ms at 99.9% monthly availability; order
  write p99 < 500 ms; inventory gRPC p99 < 50 ms; webhook delivery 99.5%
  within 60 s. Error budgets govern release pace.
- **Security:** OAuth 2.0 + JWT bearer at the gateway; API keys for
  partners; webhook signatures; OWASP API Top 10 checklist in CI; no
  credential material in logs.
- **Rate tiers:** `public` 60/min, `partner-standard` 600/min,
  `partner-premium` 6,000/min; IETF rate-limit headers on every response.
- **Data integrity:** order + outbox atomicity; idempotent order placement;
  replayable webhook log retained 30 days.
- **Operability:** OTel-style traces end to end; twelve-factor
  configuration; health endpoints; benchmark snapshot per release.

## Inputs/Datasets

- The full chapter (reference architecture, NFRs, milestone plan).
- Synthetic Northwind datasets: `..\..\datasets\northwind_robotics\parts.csv`,
  `orders.csv`, `order_lines.csv`, `inventory.csv`, `customers.csv`,
  `telemetry_events.jsonl`, `api_access_log.jsonl`.
- In-process fakes for broker, payments, and identity provider.

## The Four-Milestone Delivery Plan

| Milestone | Theme | Exit criteria |
|-----------|-------|---------------|
| M1 (weeks 1–4) | REST core | catalog + orders REST surface green on contract tests; RFC 9457 everywhere; keyset pagination; idempotency replay test passing. |
| M2 (weeks 5–8) | Read model + internal RPC | GraphQL read model live with depth limiting; inventory gRPC service with streaming `WatchStock`; gateway auth + rate tiers. |
| M3 (weeks 9–12) | Async platform | outbox relay, signed webhooks with delivery log and replay, SSE telemetry stream; AsyncAPI specs linted in CI. |
| M4 (weeks 13–16) | Production hardening | OTel traces across all surfaces; SLO dashboards; conformance checker gating merges; load and failure-mode test evidence; portal published. |

## Steps

1. **M1:** REST catalog + orders core with keyset pagination, date
   versioning, RFC 9457 errors, idempotency keys, and contract tests.
2. **M2:** GraphQL read model with depth limits and persisted queries;
   inventory gRPC service; gateway-simulating middleware for auth and rate
   tiers with IETF headers.
3. **M3:** outbox relay, signed webhooks with delivery log and replay
   (Capstone 21.4 folded in), SSE telemetry stream; OpenAPI + AsyncAPI
   manifests under conformance CI.
4. **M4:** OTel-style trace context propagated across all surfaces; SLO
   definitions with a load test harness; chaos drill (kill inventory
   mid-order) demonstrating circuit-breaker behavior; developer-portal
   pages generated from the specs.
5. **Final:** a written design review — decision-card rationale per
   surface, frontier assessment for HTTP/3 and MCP, and a one-year
   evolution plan.

## Acceptance Criteria

- [ ] All five surfaces respond per spec in one offline in-process test
      run.
- [ ] Conformance checker passes on the full `specs\` folder.
- [ ] SLOs measured green against a recorded load test.
- [ ] Chaos drill produces the designed failure behavior with zero data
      loss (outbox replay verified).
- [ ] Rubric score ≥ 16/20 with no dimension below 3 (correctness,
      resilience, operability, governance, craft).

## Stretch Goals

- Canary deployment simulation with traffic splitting.
- MCP tool surface generated from the OpenAPI spec for the read-only
  catalog.
- Regional-affinity design document for a hypothetical EU expansion.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q                       # milestone smoke tests
python starter.py --milestone 1 --dry-run # plan of work per milestone
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics** — the Grand
Capstone rubric scores five dimensions 0–4 (correctness, resilience,
operability, governance, craft); passing is ≥ 16 with no dimension below 3.
