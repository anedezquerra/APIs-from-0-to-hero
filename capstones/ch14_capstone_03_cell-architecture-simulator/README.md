# Capstone 14.3 — Cell Architecture Simulator [mid]

> Quantify, rather than assert, the over-admission of cell-based rate limiting.

## Objective

Simulate three enforcement topologies over the same seeded multi-client
timeline — one exact global limiter, R=4 local limiters at limit/R with no
sync, and R=4 local limiters with periodic sync — sweep the sync interval,
and verify the published over-admission bound.

## Inputs/Datasets

- The chapter's simulation harness pattern.
- A seeded multi-client timeline generator you write (10 keys, Poisson-ish
  arrivals, one adversarial key).

## Steps

1. Implement three enforcement topologies over the same timeline: global
   (exact), R=4 local at limit/R with no sync, and R=4 local with a sync
   every Δ seconds (reconciliation subtracts observed remote consumption).
2. Sweep Δ ∈ {0.1, 0.5, 1.0, 5.0} s and record worst-case per-window
   admissions for the adversarial key.
3. Produce a pgfplots-ready table of over-admission versus Δ.
4. Verify the bound: admissions ≤ N + R · r · Δ.

## Acceptance Criteria

- [ ] Global topology never exceeds the limit; no-sync topology's overshoot
      matches the R× prediction.
- [ ] Sync topology's measured overshoot respects the published bound at
      every Δ.
- [ ] All results reproducible from one seed.

## Stretch Goals

- Add a cell-failure event mid-timeline and show the consistent-hash remap
  confines counter loss to 1/C of keys.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
