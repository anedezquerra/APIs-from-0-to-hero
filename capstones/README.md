# Capstones — "Mastering APIs: From Zero to Production Guru"

This tree holds starter scaffolds for the book's **110 capstone projects**
(22 chapters × 5, one per difficulty band: `[junior]`, `[mid]`, `[senior]`,
`[staff]`).

- `capstones\_template\` — the canonical starter template every capstone
  folder is instantiated from.
- `capstones\chNN_capstone_MM_<slug>\` — a starter scaffold for capstone MM
  of chapter NN. **40 of the 110 capstones have full scaffolds** (marked ✅
  below); the rest are indexed from the chapter specifications (📖 — copy
  `_template\` to begin one).

## How to use the scaffolds (PowerShell)

```powershell
# 1. Pick a capstone folder, e.g.:
cd capstones\ch02_capstone_01_robust-cli-downloader

# 2. Read README.md — Objective, Inputs/Datasets, Steps, Acceptance
#    Criteria, Stretch Goals are the contract you build against.

# 3. Create an isolated environment and install the minimal deps:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 4. Run the smoke tests — they pass out of the box:
python -m pytest -q          # from inside the capstone folder
# or from the repo root:
python -m pytest capstones\ch02_capstone_01_robust-cli-downloader -q

# 5. Implement the TODO functions in starter.py; unskip the TODO tests in
#    test_starter.py and add your own until every acceptance box checks.
```

Conventions: Python 3.11+, fully typed, **offline-first** (no network, no
API keys — simulate external services with deterministic fakes), seeded
randomness, synthetic Northwind Robotics data only. Shared datasets live at
`datasets\northwind_robotics\` (`parts.csv`, `orders.csv`, `order_lines.csv`,
`inventory.csv`, `customers.csv`, `telemetry_events.jsonl`,
`api_access_log.jsonl`); reference them from a capstone folder as
`..\..\datasets\northwind_robotics\<file>`.

## Grading

Score submissions against the book's **Appendix: Solutions & Grading
Rubrics**. Each capstone README's acceptance criteria are the minimum bar;
the appendix rubrics grade correctness, resilience, operability,
governance, and craft.

---

## Chapter 0 — Introduction: The API Economy & How to Use This Book

| # | Capstone | Level | Summary |
|---|----------|-------|---------|
| 0.1 | Contract Archaeology | [junior] | Reverse-engineer the mini API's complete contract by black-box observation and write it down formally. |
| 0.2 | Honest Benchmarks | [mid] | Defensible latency study of the mini API under three load shapes, exposing where mean and p99 diverge. |
| 0.3 | Failure Taxonomy Field Guide | [mid] | One scripted, reproducible demo per failure-taxonomy category, each with detection evidence and a playbook entry. |
| 0.4 | Budgets and Breakers for the Mini API | [senior] | Timeouts, retry policy, circuit breaker, and a live error-budget burn calculation on the mini API. |
| 0.5 | API Platform Governance Starter | [staff] | Minimum governance plane for a 20-team org: catalog schema, contract linter, deprecation policy, maturity reports. |

## Chapter 1 — The HTTP Wire Protocol: HTTP/1.1, HTTP/2 & HTTP/3

| # | Capstone | Level | Summary |
|---|----------|-------|---------|
| 1.1 | From-Scratch HTTP/1.1 Server | [junior] | Minimal but correct HTTP/1.1 server over raw `socketserver` serving the Northwind parts catalog. |
| 1.2 | Chunked Streaming Proxy | [mid] | Localhost reverse proxy relaying `Transfer-Encoding: chunked` responses with defensive parsing. |
| 1.3 | HPACK-Lite Header Encoder | [mid] | Pure-stdlib encoder for an HPACK subset: static-table indexing, literal-with-incremental-indexing, integer prefix coding. |
| 1.4 | Protocol Fingerprinting & Frame Dissection Toolkit | [senior] | Passive analysis CLI that classifies captured byte streams (HTTP/1.1 text, h2 preface) and dissects frames. |
| 1.5 | HTTP Version Latency Profiler & Wire-Debugging Workbench | [staff] | Local benchmark harness quantifying connection-setup and per-request costs across HTTP/1.1 configurations. |

## Chapter 2 — Consuming APIs in Python: From urllib to httpx

| # | Capstone | Level | Summary | Scaffold |
|---|----------|-------|---------|----------|
| 2.1 | Robust CLI Downloader | [junior] | `nrget`: a PowerShell-friendly CLI that downloads a part's datasheet with explicit timeouts, atomic `.part`-rename writes, and typed exit codes. | ✅ `ch02_capstone_01_robust-cli-downloader` |
| 2.2 | Rate-Limit-Aware Catalog Crawler | [mid] | Crawl a 500-part cursor-paginated catalog under a published 5 req/s limit without steady-state 429s. | ✅ `ch02_capstone_02_rate-limit-catalog-crawler` |
| 2.3 | Typed SDK Wrapper with Full Test Matrix | [mid] | Publish a local `northwind-parts-sdk`: pydantic models, resilient client, pagination iterators, ≥15-scenario offline fault matrix. | ✅ `ch02_capstone_03_typed-sdk-wrapper` |
| 2.4 | Chaos-Client Harness | [senior] | A fault-injection transport that empirically proves the resilient client survives a scripted fault gauntlet. | ✅ `ch02_capstone_04_chaos-client-harness` |
| 2.5 | Async Concurrent Fetcher with Bounded Concurrency | [staff] | `httpx.AsyncClient` fetcher draining a 10,000-item queue at maximum throughput under the provider's limit, plus a design memo. | ✅ `ch02_capstone_05_async-concurrent-fetcher` |

## Chapter 3 — The REST Architectural Style & Resource Design

| # | Capstone | Level | Summary |
|---|----------|-------|---------|
| 3.1 | Model the Library Domain | [junior] | Practice pure resource modeling on an unfamiliar (library) domain. |
| 3.2 | Run and Extend the Stdlib Catalog | [junior] | Operate the chapter's stdlib catalog service and prove its uniform-interface behavior. |
| 3.3 | Productionize the URI Linter | [mid] | Turn the chapter's URI linter into a governance tool a platform team could run in CI. |
| 3.4 | Port an RPC API to Resource Orientation | [senior] | Execute the chapter's migration doctrine on an RPC-style API. |
| 3.5 | Design-Review Report on a Public API | [staff] | Staff-grade architectural critique of a real, public API. |

## Chapter 4 — Data on the Wire: Serialization Formats & Data Contracts

| # | Capstone | Level | Summary |
|---|----------|-------|---------|
| 4.1 | NDJSON Inventory Log Shipper | [junior] | Robust local log shipper watching a directory of NDJSON inventory logs. |
| 4.2 | Schema-Validation Middleware | [mid] | Package the chapter's schema pipeline as reusable validation middleware. |
| 4.3 | Hand-Rolled Protobuf Codec Extension | [senior] | Extend the mini protobuf codec into a two-message system. |
| 4.4 | Negotiation-Aware Cache Key Tool | [senior] | CLI that derives correct cache keys from recorded HTTP request/response pairs. |
| 4.5 | Format-Migration CLI for a Dataset | [staff] | Design and implement a migration tool that converts a dataset across serialization formats. |

## Chapter 5 — Client-Side Security: API Keys, OAuth 2.0/OIDC & JWT for Consumers

| # | Capstone | Level | Summary |
|---|----------|-------|---------|
| 5.1 | HMAC-Signed Webhook Consumer | [junior] | Build the receiving half of a signed-webhook contract. |
| 5.2 | Full PKCE CLI | [mid] | Ship a complete command-line OAuth 2.0 client with the PKCE flow. |
| 5.3 | JWT Security Linter | [mid] | Static analyzer that flags common JWT-handling mistakes. |
| 5.4 | Token-Broker Service | [senior] | Implement a local token-broker service issuing scoped tokens. |
| 5.5 | Red-Team Your Own Client | [staff] | Adversarially review the chapter's code — and your own client. |

## Chapter 6 — Building Production REST APIs with FastAPI

| # | Capstone | Level | Summary | Scaffold |
|---|----------|-------|---------|----------|
| 6.1 | Todo API with a Full Test Suite | [junior] | Minimal but complete FastAPI todo service: repository behind a protocol, `response_model` everywhere, ≥10 TestClient tests. | ✅ `ch06_capstone_01_todo-api-test-suite` |
| 6.2 | Inventory API with a SQLite Repository | [mid] | Warehouse inventory API with in-memory *and* SQLite repositories behind one protocol, settings-selected, with a real readiness probe. | ✅ `ch06_capstone_02_inventory-api-sqlite` |
| 6.3 | Plugin-Style Dependency-Injection Architecture | [senior] | Repositories, notifiers, and pricing policies as registry plugins selected by settings and swapped per test via `dependency_overrides`. | ✅ `ch06_capstone_03_plugin-di-architecture` |
| 6.4 | Async Migration of a Blocking Service | [senior] | Migrate a blocking service to correct-concurrency form, proving each step with loop-lag middleware and a concurrency benchmark. | ✅ `ch06_capstone_04_async-migration` |
| 6.5 | OpenAPI-First Generator Round-Trip | [staff] | Author `orders.openapi.yaml`, generate skeleton + typed client, and build a CI gate that fails on contract divergence. | ✅ `ch06_capstone_05_openapi-first-roundtrip` |

## Chapter 7 — Errors, Validation & Problem Details (RFC 9457)

| # | Capstone | Level | Summary |
|---|----------|-------|---------|
| 7.1 | Problem-Details Retrofit | [junior] | Retrofit uniform RFC 9457 errors onto a messy legacy service without touching success-path behavior. |
| 7.2 | Error-Code Registry & Documentation Generator | [mid] | Self-validating error registry generating Markdown catalogues and a machine-readable `errors.json`, with an orphan-code CI check. |
| 7.3 | Redaction Library with Fuzz Corpus | [mid] | Harden the chapter's scrubber into a standalone library attacked by a 50+ entry adversarial corpus with a bounded false-positive rate. |
| 7.4 | Error-Observability Dashboard Specification | [senior] | Offline error-observability prototype: metric taxonomy, declarative alert rules, replay aggregator, dashboard spec. |
| 7.5 | Chaos Error-Injection Test Harness | [staff] | In-process fault injectors proving the whole error chain — status mapping, problem shape, redaction, correlation, metrics — survives chaos. |

## Chapter 8 — Pagination, Filtering, Sorting & Field Selection

| # | Capstone | Level | Summary |
|---|----------|-------|---------|
| 8.1 | Cursor-Paginated Ledger API | [junior] | Re-implement the chapter's case study correctly as a cursor-paginated ledger API. |
| 8.2 | Filter Compiler with Property Tests | [mid] | Harden the chapter's filter compiler with property-based tests. |
| 8.3 | Pagination Benchmark Report | [mid] | Reproducible, reviewer-grade benchmark comparing pagination strategies. |
| 8.4 | Infinite-Scroll Client over Signed Cursors | [senior] | Terminal-based infinite-scroll parts browser over signed cursors. |
| 8.5 | Multi-Tenant Keyset Design | [staff] | Design and validate the pagination layer for a multi-tenant dataset. |

## Chapter 9 — API Versioning & Evolution Strategies

| # | Capstone | Level | Summary |
|---|----------|-------|---------|
| 9.1 | Add v2 to an Existing API with an Adapter Layer | [junior] | Take a single-version CRUD API and add v2 behind an adapter layer. |
| 9.2 | Media-Type Version Negotiation Middleware | [mid] | Generalize the chapter's example into reusable FastAPI content-negotiation middleware. |
| 9.3 | Production Breaking-Change CI Gate | [mid] | Harden the spec-diff listing into a breaking-change gate you would actually run on CI. |
| 9.4 | Deprecation Campaign Plan & Retirement Analytics | [senior] | Design and instrument the complete retirement program for an API version. |
| 9.5 | Version Governance at Platform Scale | [staff] | Design the versioning and retirement governance system for a whole platform. |

## Chapter 10 — Idempotency, Caching & Concurrency Control

| # | Capstone | Level | Summary | Scaffold |
|---|----------|-------|---------|----------|
| 10.1 | Idempotency-Key Client SDK | [junior] | Client half of the idempotency protocol: one key per logical operation, replayed across retries, exactly-one server mutation. | ✅ `ch10_capstone_01_idempotency-key-sdk` |
| 10.2 | Conditional-GET Sync Agent | [junior] | Catalog sync agent using ETag/`If-None-Match` that transfers bytes only when representations change. | ✅ `ch10_capstone_02_conditional-get-sync` |
| 10.3 | Optimistic-Locking Order Service | [mid] | Conditional writes (`If-Match`) for reserve/release with a read–decide–write–retry client, proven under a 100-worker storm. | ✅ `ch10_capstone_03_optimistic-locking-orders` |
| 10.4 | Cache-Policy Workbench | [senior] | Policy evaluation tool ranking cache policies by origin load, staleness window, and error resilience over a scripted timeline. | ✅ `ch10_capstone_04_cache-policy-workbench` |
| 10.5 | Correctness Audit of a Retry-Capable Gateway | [staff] | Full duplicate-safety audit: retry-source inventory, idempotency classification linter, remediation and telemetry plan. | ✅ `ch10_capstone_05_gateway-retry-audit` |

## Chapter 11 — Asynchronous & Event-Driven APIs: Webhooks, SSE & WebSockets

| # | Capstone | Level | Summary |
|---|----------|-------|---------|
| 11.1 | Signed Webhook Receiver for Robot Alerts | [junior] | Build the consumer half of a webhook contract from scratch. |
| 11.2 | Webhook Delivery Service with DLQ and Replay | [mid] | Provider half: queue, bounded jittered retries, dead-letter queue, replay. |
| 11.3 | Resumable SSE Fleet Dashboard Backend | [mid] | Multi-channel SSE feed with correct `Last-Event-ID` resume semantics. |
| 11.4 | Bidirectional Robot Control Channel over WebSockets | [senior] | Production-shaped WebSocket service with subprotocol negotiation. |
| 11.5 | Event-Contract Governance Platform | [staff] | Stand up the contract-governance layer for Northwind's event catalog. |

## Chapter 12 — GraphQL: Schema-Driven APIs

| # | Capstone | Level | Summary |
|---|----------|-------|---------|
| 12.1 | Catalog Schema from Scratch | [junior] | Re-implement the catalog schema without copying the chapter's. |
| 12.2 | N+1 Hunter | [mid] | Find and fix N+1 query patterns in a deliberately naive GraphQL service. |
| 12.3 | Cost-Control Gateway | [mid] | Build the static query-cost analysis gate as a standalone, schema-agnostic library. |
| 12.4 | APQ Production Gateway | [senior] | Ship the lab as an operations-locked gateway with automatic persisted queries. |
| 12.5 | Federated Robotics Graph | [staff] | Split the catalog into two subgraphs behind a federation gateway. |

## Chapter 13 — gRPC & High-Performance RPC

| # | Capstone | Level | Summary |
|---|----------|-------|---------|
| 13.1 | Unary Status Service with Deadline Discipline | [junior] | Stand up a single-RPC gRPC service and prove deadline/timeouts are understood. |
| 13.2 | Server-Streaming Telemetry Monitor | [mid] | Resilient streaming consumer that respects flow control. |
| 13.3 | Bulk Ingestion with Rich Validation Errors | [mid] | Client-streaming ingestion where bad data produces rich per-record errors. |
| 13.4 | Bidirectional Control Plane with a Full Interceptor Stack | [senior] | Production-shaped bidi service: windowed flow control, auth + logging + metrics interceptors, retry policy. |
| 13.5 | Edge Gateway: Transcoding plus Load-Balancing Postmortem Lab | [staff] | Reproduce the chapter's war story in miniature, fix it three ways, and expose the service safely to JSON clients. |

## Chapter 14 — Rate Limiting, Throttling & Quota Systems

| # | Capstone | Level | Summary | Scaffold |
|---|----------|-------|---------|----------|
| 14.1 | Prove the Algorithms | [junior] | Reimplement the five limiters from their mathematical definitions, port the chapter's 14 tests, then break each on purpose. | ✅ `ch14_capstone_01_prove-the-algorithms` |
| 14.2 | Header-Complete Middleware | [mid] | Platform-grade rate-limit middleware: Redis-backed limiter behind a protocol, RFC 9457 429 bodies, fail-open degraded signal. | ✅ `ch14_capstone_02_header-complete-middleware` |
| 14.3 | Cell Architecture Simulator | [mid] | Quantify the over-admission of cell-based limiting across global/local/sync topologies and verify the published bound. | ✅ `ch14_capstone_03_cell-architecture-simulator` |
| 14.4 | Adaptive Limits with AIMD | [senior] | Build and tune an AIMD-adaptive per-tenant limiter tracking a moving capacity signal; find the tuning knee. | ✅ `ch14_capstone_04_adaptive-aimd-limiter` |
| 14.5 | Rate-Limiting Architecture for Northwind at 100k rps | [staff] | Complete design document: tiers, topologies, header contract, failure runbook, and cost model for 10⁵ rps in five regions. | ✅ `ch14_capstone_05_northwind-100k-architecture` |

## Chapter 15 — Microservices & Resilient Inter-Service Communication

| # | Capstone | Level | Summary |
|---|----------|-------|---------|
| 15.1 | Breaker Under a Microscope | [junior] | Reimplement the chapter's circuit breaker and observe every state transition. |
| 15.2 | Latency Chaos and the Price of Hedging | [mid] | Extend the drill to latency faults and measure what hedged requests cost. |
| 15.3 | Production Outbox: Retry, DLQ, Ordering | [mid] | Harden the outbox listing into the relay you would actually ship. |
| 15.4 | Measure the Retry-Amplification Theorem | [senior] | Four-hop amplification testbed verifying the chapter's retry-amplification theorem. |
| 15.5 | Resilience Architecture for Fleet Telemetry | [staff] | Produce and defend a complete resilience design for fleet telemetry. |

## Chapter 16 — API Security Engineering (OWASP API Security Top 10)

| # | Capstone | Level | Summary | Scaffold |
|---|----------|-------|---------|----------|
| 16.1 | BOLA Hunter | [junior] | Notes API with a deliberately missing ownership check, an exploit script, then the fix and the 403 regression test. | ✅ `ch16_capstone_01_bola-hunter` |
| 16.2 | Scope Forge & Token Gauntlet | [mid] | Toy resource server with full token validation and a scope model, attacked by a seven-forgery battery. | ✅ `ch16_capstone_02_scope-forge-token-gauntlet` |
| 16.3 | SSRF Bunker | [mid] | Harden a webhook-tester feature against SSRF with the seven-layer gauntlet over a simulated adversary network. | ✅ `ch16_capstone_03_ssrf-bunker` |
| 16.4 | Threat-Model Pipeline | [senior] | Turn the STRIDE worksheet into a CI gate that fails when endpoints ship without completed threat-model rows. | ✅ `ch16_capstone_04_threat-model-pipeline` |
| 16.5 | Full Red Team / Blue Team Exercise | [staff] | Two-sided exercise on a multi-service topology: exploits as failing contract tests, fixes that keep the functional suite green. | ✅ `ch16_capstone_05_red-blue-exercise` |

## Chapter 17 — Deployment & Infrastructure: Containers, Gateways & Edge

| # | Capstone | Level | Summary |
|---|----------|-------|---------|
| 17.1 | Harden the Image | [junior] | Take a naive single-stage Dockerfile for the Orders service and harden it. |
| 17.2 | Prove the Drain Under Load | [mid] | Extend the graceful-shutdown demo and prove connection draining under load. |
| 17.3 | Manifest Review Board | [mid] | Run the chapter's manifest set through a formal review board. |
| 17.4 | Gate Tuner | [senior] | Turn the canary listing from a demo into a tuned deployment gate. |
| 17.5 | Zero-Downtime Reference Architecture | [staff] | Design and document the complete zero-downtime deployment architecture. |

## Chapter 18 — Observability & SRE for APIs

| # | Capstone | Level | Summary | Scaffold |
|---|----------|-------|---------|----------|
| 18.1 | Trace Context Conformance Pack | [junior] | Extend the `traceparent` parser into a conformance checker over a 25-case corpus plus a 500-case round-trip property test. | ✅ `ch18_capstone_01_trace-context-conformance` |
| 18.2 | RED Metrics for a Real Route Set | [mid] | Per-endpoint RED metrics (rate, errors, duration) over four routes with an exactly-enforced cardinality bound. | ✅ `ch18_capstone_02_red-metrics-route-set` |
| 18.3 | SLO Workbench | [mid] | Turn the burn-rate alerter into a policy design tool; defend one design change against three scripted incidents. | ✅ `ch18_capstone_03_slo-workbench` |
| 18.4 | Queue Propagation End to End | [senior] | One trace across HTTP *and* a message broker: context injection, CONSUMER spans, span links for batches. | ✅ `ch18_capstone_04_queue-propagation` |
| 18.5 | Incident Program in a Box | [staff] | Complete operational loop — SLOs, runbooks, game day, blameless postmortem — for the fleet-telemetry platform. | ✅ `ch18_capstone_05_incident-program-in-a-box` |

## Chapter 19 — Testing & Quality Engineering for APIs

| # | Capstone | Level | Summary | Scaffold |
|---|----------|-------|---------|----------|
| 19.1 | A Second Consumer | [junior] | Extend the contract suite with a `billing-service` consumer and watch usage-based verification catch a breaking change. | ✅ `ch19_capstone_01_second-consumer` |
| 19.2 | Property Suite for a New Resource | [mid] | Bring a new `/warehouses` resource under property-based and fuzz coverage; find and shrink two planted bugs. | ✅ `ch19_capstone_02_property-suite-warehouses` |
| 19.3 | Record–Replay Cassette Library | [mid] | Build a minimal VCR for `httpx` with sanitization hooks, and demonstrate where cassettes rot. | ✅ `ch19_capstone_03_record-replay-cassettes` |
| 19.4 | Capacity Report from a Knee Sweep | [senior] | Capacity analysis defended with Little's Law: predicted vs measured knees, headroom recommendation, CI perf budget. | ✅ `ch19_capstone_04_capacity-knee-sweep` |
| 19.5 | Quality-Gate Architecture for a Fleet | [staff] | Design the quality-gate architecture for a fictional ten-service Northwind fleet. | ✅ `ch19_capstone_05_quality-gate-fleet` |

## Chapter 20 — API Lifecycle, Governance & Developer Experience

| # | Capstone | Level | Summary |
|---|----------|-------|---------|
| 20.1 | Three New Rules for the Fleet | [junior] | Extend the Northwind ruleset with three custom lint rules. |
| 20.2 | Docs-as-Code Pipeline | [mid] | Assemble a lint → docs → publish pipeline. |
| 20.3 | TTFC Instrumentation Pack | [mid] | Extend the time-to-first-call funnel analyzer from report to decision tool. |
| 20.4 | Sunset Campaign for Fleet API v1 | [senior] | Design and simulate the full retirement of a legacy API version. |
| 20.5 | Platform ROI Scorecard & Governance Operating Model | [staff] | Design the quarterly platform review for a fictional organization. |

## Chapter 21 — Synthesis, Reference Architectures & Future Directions

| # | Capstone | Level | Summary | Scaffold |
|---|----------|-------|---------|----------|
| 21.1 | Extend the Decision Advisor | [junior] | Deepen the protocol-decision advisor into a usable team tool: questionnaire mode, a seventh criterion, `--explain`. | ✅ `ch21_capstone_01_decision-advisor` |
| 21.2 | Governance Toolchain | [mid] | Grow the conformance checker into a team-grade lint gate with new rules, JSON reports, and changed-only CI mode. | ✅ `ch21_capstone_02_governance-toolchain` |
| 21.3 | Multi-Protocol Read/Write Split | [senior] | REST writes, GraphQL reads, gRPC internal coordination over one shared store — with a proven consistency test. | ✅ `ch21_capstone_03_multiprotocol-read-write` |
| 21.4 | Webhook Notification Pipeline with Outbox Replay | [senior] | Partner-notification subsystem end to end: outbox relay, HMAC-signed webhooks, delivery log, replay, AsyncAPI docs. | ✅ `ch21_capstone_04_webhook-outbox-pipeline` |
| 21.5 | The Grand Capstone — Northwind Robotics API Platform | [staff] | The complete governed, observable platform: five API surfaces, four milestones, rubric ≥ 16/20. Larger scaffold with `services/`, `specs/`, `tests/`. | ✅ `ch21_capstone_05_grand-capstone-platform` |
