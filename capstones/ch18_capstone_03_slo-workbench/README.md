# Capstone 18.3 — SLO Workbench [mid]

> Turn the chapter's burn-rate alerting listing into a policy design tool and defend one design change with data.

## Objective

A policy design tool over scripted incidents: encode three incidents (a
3-minute total outage, a 6-hour 2% error bleed, a flapping
30s-on/30s-off failure), run the stock burn-rate policy table against each,
record time-to-page and false positives, then propose one modification and
show its effect on all three.

## Inputs/Datasets

- The chapter's Listing 18.5 (burn-rate alerter).
- Three scripted incidents you write, each with a distinct seed.

## Steps

1. Encode the three incidents as timeline generators with distinct seeds.
2. Run the stock policy table against each; record time-to-page and false
   positives.
3. Propose one modification (e.g. a third window pair at 3×/1d+2h, or a
   flapping-damping reset rule) and show its effect on all three incidents.
4. Write a one-page memo: which table ships, and why, in budget-consumption
   terms.

## Acceptance Criteria

- [ ] All three incidents produce a documented, reproducible alert
      timeline.
- [ ] The flapping incident is shown to reset-and-refire under the stock
      table, and your modification addresses it.
- [ ] The memo states budget math for every policy row.

## Stretch Goals

- Alert-resolution tracking (when would each page auto-resolve?) and mean
  time to resolve per policy.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
