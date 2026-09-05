# Capstone 14.4 — Adaptive Limits with AIMD [senior]

> Build and tune an AIMD-adaptive per-tenant limiter that tracks a moving capacity.

## Objective

Implement a controller that evaluates once per second — `L ← L + a` when
healthy, `L ← βL` on overload, floored at a contractual minimum — against a
seeded capacity signal oscillating between 150 and 450 rps; sweep the
`(a, β)` grid, find the knee, and write the tuning memo.

## Inputs/Datasets

- The chapter's limiter listings.
- A synthetic "capacity signal" generator you author: service capacity
  oscillates between 150 and 450 rps on a seeded schedule; overload is
  reported when admitted rate exceeds current capacity.

## Steps

1. Implement the controller: per-second evaluation, additive increase when
   healthy, multiplicative decrease on overload, floored at a contractual
   minimum.
2. Sweep `(a, β)` over a small grid; for each pair record
   time-to-first-contact, steady-state oscillation amplitude, and total
   rejected load.
3. Identify the knee: the fastest `a` whose β-paired oscillation never
   exceeds capacity by more than 10%.
4. Write the tuning memo: why multiplicative decrease is the safety
   parameter and additive increase merely the efficiency parameter.

## Acceptance Criteria

- [ ] Controller never lets admitted rate exceed capacity by > 10% for more
      than one evaluation interval, for the tuned `(a, β)`.
- [ ] Floor is never violated even under sustained overload.
- [ ] Grid results and the knee are reproducible from the seed; the memo
      quantifies the asymmetry argument.

## Stretch Goals

- Per-tenant fairness: divide recovered headroom proportional to recent
  demand rather than equally.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
