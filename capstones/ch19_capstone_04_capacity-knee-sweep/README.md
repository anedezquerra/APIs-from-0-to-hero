# Capstone 19.4 — Capacity Report from a Knee Sweep [senior]

> Produce a capacity analysis for a service using the chapter's load harness, defended with Little's Law.

## Objective

Predict capacity analytically (`c/S`, with the ρ → 1 latency shape), measure
it with open-model sweeps at three `work_ms` settings, cross-check with a
closed-model run and `L = λW`, and write the one-page report: knee,
recommended provisioning headroom, and the perf budget to encode in CI.

## Inputs/Datasets

- The chapter's `code\ch19\` load harness.
- A workload app with tunable `work_ms` and `max_concurrent`.

## Steps

1. Predict capacity analytically: `c/S`, with ρ → 1 latency shape.
2. Run open-model sweeps at three `work_ms` settings; tabulate knee points;
   compare with prediction.
3. Cross-check with a closed-model run and `L = λW`.
4. Write the one-page report: knee, recommended provisioning headroom, and
   the perf budget to encode in CI.

## Acceptance Criteria

- [ ] Predicted and measured knees agree within a factor of two, with the
      discrepancy explained.
- [ ] The report includes a knee table, a Little's Law cross-check, and an
      explicit headroom recommendation.
- [ ] No wall-clock assertion anywhere; numbers labeled illustrative.

## Stretch Goals

- A coordinated-omission buggy scheduler variant; quantify how much it
  overstates capacity.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
