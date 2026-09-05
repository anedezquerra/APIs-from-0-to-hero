# Capstone 19.2 — Property Suite for a New Resource [mid]

> Bring a second resource under property-based and fuzz coverage.

## Objective

Add a `/warehouses` resource (fields: `code`, `city`, `capacity_m2`) to the
robot-registry app with RFC 9457 error handling, then attack it: hostile-
payload Hypothesis tests encoding the three universal invariants, an
extended fuzzer schema, and two planted bugs that must be found and shrunk.

## Inputs/Datasets

- The chapter's `code\ch19\` suite (Hypothesis tests, fuzzer).
- The new `/warehouses` resource you add to the registry.

## Steps

1. Implement the resource with RFC 9457 error handling.
2. Write hostile-payload Hypothesis tests encoding the three universal
   invariants (no 5xx, schema-valid responses, problem-shaped errors).
3. Extend the fuzzer's schema excerpt and candidate generation for the new
   fields.
4. Plant two distinct bugs (a 500 trigger; a schema-violating 201) and
   confirm both are found and shrunk.

## Acceptance Criteria

- [ ] `derandomize=True` suites pass repeatably.
- [ ] Both planted bugs produce minimal shrunk reproducers.
- [ ] Zero 5xx and zero non-problem 4xx across the campaign.

## Stretch Goals

- A rule-based stateful machine over create/read/update sequences for
  warehouses, with a local model oracle.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
