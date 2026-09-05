# Capstone 14.1 — Prove the Algorithms [junior]

> Reproduce the chapter's entire rate-limiter proof sheet from a standing start, then break it on purpose.

## Objective

Reimplement the five limiters (fixed window, sliding log, sliding window,
token bucket, GCRA) from their mathematical definitions only — close the
book; keep the `Decision` contract — port the chapter's 14 tests unmodified,
then introduce one deliberate bug per algorithm and record which test
catches each.

## Inputs/Datasets

- The chapter's Listings 14.1–14.2 (contract shape only — reimplement from
  the math).
- No datasets.

## Steps

1. Reimplement the five limiters from their mathematical definitions only
   (keep the `Decision` contract).
2. Port the chapter's 14 tests to your implementation unmodified.
3. Introduce one deliberate bug per algorithm (e.g. forget the `max` in
   GCRA's TAT update) and record which test catches each.
4. Write one new test: the fixed window's 2x burst with a *non-integer*
   window (e.g. `W = 1.5`).

## Acceptance Criteria

- [ ] All 14 ported tests pass against your reimplementation.
- [ ] Every seeded bug is caught by at least one existing test; you can
      name the mapping.
- [ ] The new non-integer-window burst test proves 20 admissions in a
      sub-window interval.

## Stretch Goals

- Property-test the sliding log with random seeded timelines, asserting the
  exactness invariant on every run.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
