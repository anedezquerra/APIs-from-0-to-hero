# Capstone 21.3 — Multi-Protocol Read/Write Split [senior]

> Build a domain where writes are REST, reads are GraphQL, and internal coordination is gRPC — over one shared store — and prove consistency.

## Objective

Split the chapter's platform skeleton into a write service (REST, idempotent
commands) and a read service (GraphQL projections), propagate writes through
an outbox-backed event stream (in-process broker fake with a broker-shaped
interface), model the internal inventory check as a gRPC contract, and prove
with a deterministic concurrency test that orders never oversell stock and
the read model converges within bounded polls.

## Inputs/Datasets

- The chapter's platform skeleton listing.
- Synthetic Northwind catalog/orders datasets:
  `..\..\datasets\northwind_robotics\parts.csv`,
  `..\..\datasets\northwind_robotics\orders.csv`,
  `..\..\datasets\northwind_robotics\inventory.csv`.

## Steps

1. Split the skeleton into a write service (REST, idempotent commands) and
   a read service (GraphQL projections).
2. Propagate writes to the read store through an outbox-backed event stream
   (in-process broker fake is fine; keep the interface broker-shaped).
3. Model the internal inventory check as a gRPC contract (write the
   `.proto`; an in-process stub implementation is acceptable offline).
4. Write the consistency test: concurrent orders never oversell stock; the
   GraphQL read model converges within a bounded number of polls.

## Acceptance Criteria

- [ ] REST writes return RFC 9457 errors and honor idempotency keys.
- [ ] GraphQL reads never expose uncommitted state.
- [ ] The concurrency test passes deterministically in 100 runs.
- [ ] OpenAPI and GraphQL SDL artifacts both exist and pass the Project-2
      checker.

## Stretch Goals

- CDC-style lag metric on the read model and an SLO on projection
  freshness.
- Simulate a broker outage and show recovery without loss.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
