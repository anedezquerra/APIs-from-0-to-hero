# Capstone 2.2 — Rate-Limit-Aware Catalog Crawler [mid]

> Crawl the entire paginated catalog of an instrumented stub that enforces a published 5 req/s limit and answers `429 + Retry-After` when exceeded — without ever being throttled in steady state.

## Objective

Build a crawler that drains a cursor-paginated parts catalog while staying
strictly under the provider's published rate limit. The point is discipline:
a client-side token bucket paces every request, retries honor `Retry-After`
exactly, and the achieved rate is *evidenced from recorded timestamps*, not
asserted from wall-clock.

## Inputs/Datasets

- An extended local stub: cursor-paginated `/parts` over a 500-part
  synthetic catalog, a token-bucket limiter, and
  `RateLimit-Policy` / `Retry-After` headers (offline; MockTransport for tests).
- Reference fixture: `..\..\datasets\northwind_robotics\parts.csv`.

## Steps

1. Implement a client-side token bucket (`r = 4` tokens/s, `B = 4`) gating
   every request.
2. Wrap calls in the chapter's retry policy; `Retry-After` overrides jitter.
3. Consume pages through a cursor iterator.
4. Record per-request timestamps to a CSV; compute the achieved rate.

## Acceptance Criteria

- [ ] Full crawl completes; zero `429`s in steady state (allow one
      documented cold-start burst violation).
- [ ] Achieved sustained rate ≤ 5 req/s, evidenced from the timestamp CSV
      (not wall-clock test assertions).
- [ ] A forced-`429` MockTransport test proves `Retry-After` overrides
      jitter exactly.
- [ ] Deterministic suite: seeded RNG, injected sleep, no network.

## Stretch Goals

- Adaptive bucket that lowers `r` on 429 and recovers slowly
  (additive-increase).
- Parallel crawlers sharing one process-wide bucket.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
