# Capstone 18.2 — RED Metrics for a Real Route Set [mid]

> Extend the chapter's metrics listing into a per-endpoint RED story for Northwind Robotics' four public routes.

## Objective

Rate, errors, and duration per route with disciplined cardinality: counter
and histogram carry `route` (template only) and `status_class`
(`2xx`/`4xx`/`5xx`) attributes and nothing else; 2,000 seeded synthetic
requests drive a per-route RED table; an assertion pins the exported series
count to routes × status classes, exactly.

## Inputs/Datasets

- The chapter's Listing 18.3 (metrics pipeline with `InMemoryMetricReader`).
- Routes: `POST /fleet/telemetry`, `GET /fleet/status`, `GET /fleet/{id}`,
  `GET /health`.
- Reference fixture: `..\..\datasets\northwind_robotics\api_access_log.jsonl`.

## Steps

1. Record counter and histogram with attributes `route` (template only) and
   `status_class` — nothing else.
2. Drive 2,000 seeded synthetic requests with a per-route latency model and
   a 0.2% error rate on one route.
3. Read back the `InMemoryMetricReader` and render a per-route RED table
   (rate, error ratio, p50/p99 from bucket counts).
4. Prove the cardinality bound: assert the exported series count equals
   routes × status classes, exactly.

## Acceptance Criteria

- [ ] RED table prints with per-route error ratios matching the seeded
      model within sampling jitter.
- [ ] Series-count assertion passes; adding a `user_id` label makes it fail
      loudly (demonstrate, then revert).
- [ ] Everything deterministic under one seed; no network.

## Stretch Goals

- Attach exemplars (one trace id per histogram bucket observation) and
  print one exemplar id for the p99 bucket.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
