# Capstone 19.1 — A Second Consumer [junior]

> Extend the chapter's contract suite with a new consumer to see usage-based verification in action.

## Objective

Add a `billing-service` consumer that reads only `id` and `price_cents`
from `GET /robots/{id}`, record its pact with its own provider state, and
verify both pacts against the healthy and the deliberately broken app —
proving that an unused-field rename breaks nothing while a used-field rename
fails exactly one pact.

## Inputs/Datasets

- The chapter's `code\ch19\` robot registry and `pact_mini.py`.
- Synthetic Northwind Robotics data only.

## Steps

1. Invent `billing-service`, which reads only `id` and `price_cents` from
   `GET /robots/{id}`.
2. Record its pact with its own provider state ("a robot with id 11
   exists").
3. Verify both pacts against the healthy app, then against
   `create_app(breaking=True)`.
4. Introduce a third variant that renames `name` only, and show no consumer
   pact fails.

## Acceptance Criteria

- [ ] Two pact files exist and verify green against the healthy app.
- [ ] The `sku` rename fails exactly one pact; the `name` rename fails
      none.
- [ ] Reports name the failing field with a JSONPath-style location.

## Stretch Goals

- A `can-i-deploy(provider_version)` function consulting a local JSON
  "broker" mapping versions to verified pacts.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
