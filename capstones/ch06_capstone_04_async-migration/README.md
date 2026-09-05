# Capstone 6.4 — Async Migration of a Blocking Service [senior]

> Take a deliberately blocking service (synchronous SQLite repository, `time.sleep`-simulated latency) and migrate it to correct-concurrency form, *proving* each step with an event-loop-lag middleware and a concurrency benchmark — the chapter's case-study incident, reproduced and fixed in miniature.

## Objective

Demonstrate, with numbers, that you can find and fix event-loop blocking:
capture a baseline (loop lag > 5 s under load), fix it two ways (`def`
handlers on the threadpool; `asyncio.to_thread`-wrapped repository behind
the same protocol), and write the decision memo with pool-occupancy evidence.

## Inputs/Datasets

- The provided blocking baseline service (the bug: `async def` handlers
  calling blocking code).
- A seeded dataset of 1,000 orders; a benchmark script issuing 200
  concurrent requests through `ASGITransport`.
- Reference fixture: `..\..\datasets\northwind_robotics\orders.csv`.

## Steps

1. Write the loop-lag middleware and the benchmark; capture baseline
   p50/p99 and loop lag.
2. Fix variant A: handlers become `def` (threadpool). Re-measure.
3. Fix variant B: replace the repository with an `asyncio.to_thread`-wrapped
   implementation behind the same protocol and restore `async def`.
   Re-measure.
4. Write the decision memo: which variant ships, and what limiter setting,
   with the numbers.

## Acceptance Criteria

- [ ] Baseline shows loop lag > 5 s under load; both fixed variants show
      lag < 50 ms.
- [ ] p99 under 200-way concurrency improves by an order of magnitude;
      results reproducible across three runs.
- [ ] The memo cites pool-occupancy evidence, not folklore.

## Stretch Goals

- A third variant using a genuinely async store (an `asyncio.Queue`-backed
  fake); explain the remaining differences.
- Instrument and graph threadpool queue depth during the transition.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
