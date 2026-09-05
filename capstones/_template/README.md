# Capstone <N.M> — <Title> [<difficulty>]

> One-line summary of the project. <!-- Replace with the objective in a single sentence. -->

## Objective

<!-- What you will build and the observable outcome that proves it works.
     Keep it to 2–5 sentences, faithful to the chapter's capstone spec. -->

## Inputs/Datasets

<!-- Synthetic Northwind Robotics data only — never real PII or credentials.
     Reference shared datasets with repo-relative paths, e.g.:
       ..\..\datasets\northwind_robotics\parts.csv
       ..\..\datasets\northwind_robotics\telemetry_events.jsonl
     Known shared fixtures: parts.csv, orders.csv, order_lines.csv,
     inventory.csv, customers.csv, telemetry_events.jsonl, api_access_log.jsonl.
     If the project generates its own fixtures, say how they are seeded. -->

## Steps

<!-- 3–7 ordered steps. Keep each step small and verifiable; every step
     should map to at least one acceptance criterion below. -->

1. TODO: first step.
2. TODO: second step.

## Acceptance Criteria

<!-- Every box must be checkable by a test, a file diff, or a written
     artifact. Do not add criteria you cannot verify offline. -->

- [ ] TODO: criterion 1.
- [ ] TODO: criterion 2.

## Stretch Goals

<!-- Optional extensions for stronger submissions. Keep them incremental. -->

- TODO: stretch goal.

## Setup & Run (PowerShell)

```powershell
# From this folder:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q          # or from the repo root: python -m pytest capstones\<this-folder> -q
```

Everything runs offline. Randomness is seeded; no wall-clock assertions in tests.

## Grading

Score your submission against the book's **Appendix: Solutions & Grading
Rubrics**. The acceptance criteria above are the minimum bar; the rubric
covers correctness, resilience, operability, governance, and craft.
