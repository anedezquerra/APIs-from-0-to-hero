# Capstone 2.5 — Async Concurrent Fetcher with Bounded Concurrency [staff]

> Design and validate an `httpx.AsyncClient`-based fetcher that drains a 10,000-item work queue from the stub at maximum throughput *without* tripping the provider's rate limit, exhausting the pool, or losing backpressure — and write the design memo defending every knob.

## Objective

Build an async fetcher with bounded concurrency (`asyncio.Semaphore`, not
unbounded `gather`), pool limits aligned to the semaphore, a process-wide
token bucket below the published 50 req/s limit, whole-fetcher backoff on
429, async-adapted retry budgets, and clean cancellation — then defend every
knob in a written design memo (Little's-law sizing, pool vs. semaphore
alignment, failure-mode table).

## Inputs/Datasets

- Instrumented stub: 200-part synthetic catalog, per-IP token bucket at
  50 req/s, injected latency jitter (5–200 ms, seeded).
- Reference fixture: `..\..\datasets\northwind_robotics\parts.csv`.

## Steps

1. Bounded concurrency via `asyncio.Semaphore`; pool limits aligned to the
   semaphore.
2. Process-wide token bucket below the published limit; `429` handling that
   backs off the *whole* fetcher, not one task.
3. Retry policy adapted for async sleep; elapsed and attempt budgets
   enforced.
4. Cancellation: one Ctrl+C (or task cancel) drains in-flight work, closes
   streams, exits cleanly with a partial-results manifest.
5. The memo: Little's-law sizing of concurrency vs. rate limit; pool vs.
   semaphore alignment; failure-mode table.

## Acceptance Criteria

- [ ] Full queue drains with zero unhandled exceptions and zero pool
      timeouts at the chosen settings.
- [ ] Sustained rate ≤ 50 req/s evidenced from stub-side logs; 429 rate
      < 0.1% after warm-up.
- [ ] Deterministic tests via `MockTransport` + injected async sleep; no
      wall-clock assertions.
- [ ] Cancellation test proves no orphan tasks and no partial artifacts.
- [ ] Design memo quantifies every knob; trade-offs and rejected
      alternatives documented.

## Stretch Goals

- Adaptive concurrency controller (AIMD on 429/latency signals).
- Fairness across multiple upstream hosts with per-host buckets.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
