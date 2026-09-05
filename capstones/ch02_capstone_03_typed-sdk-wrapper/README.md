# Capstone 2.3 — Typed SDK Wrapper with Full Test Matrix [mid]

> Publish (locally) a `northwind-parts-sdk` package: typed pydantic response models, the resilient client, pagination iterators, and a complete offline fault matrix.

## Objective

Package the chapter's resilient-client patterns as a small, fully typed SDK:
pydantic models for `Part`, `PartPage`, and `ApiError`; composed timeouts,
pooling, auth injection, hooks, and retry behind a clean public API; and a
MockTransport fault matrix proving behavior across every failure branch.

## Inputs/Datasets

- The Northwind stub endpoints (offline; MockTransport for tests).
- A hand-written JSON Schema for the `Part` resource used to
  generate/validate the pydantic model.
- Reference fixture: `..\..\datasets\northwind_robotics\parts.csv`.

## Steps

1. Model `Part`, `PartPage`, and `ApiError` as pydantic models with strict
   types.
2. Parse responses into models; map validation failures to
   `ApiContractError` with field-level context.
3. Compose timeouts, pooling, auth injection, hooks, and the retry wrapper
   behind a clean public API.
4. Build the MockTransport matrix: every status class, transport timeouts,
   mid-stream reset, truncated JSON, wrong `Content-Type`, oversized page
   count.

## Acceptance Criteria

- [ ] Public API fully typed; `mypy`-clean (or equivalent checked
      annotations) on the package.
- [ ] Fault matrix covers ≥ 15 scenarios including every taxonomy branch;
      all deterministic and offline.
- [ ] Contract errors are never retried; transient errors retry within
      budget; idempotency gate enforced on mutations.
- [ ] README (PowerShell-only instructions) documents install, usage, and
      error semantics.

## Stretch Goals

- Generate the model from the JSON Schema at build time.
- Add an async facade reusing the same core via `httpx.AsyncClient`.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
