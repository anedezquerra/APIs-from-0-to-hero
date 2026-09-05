# Capstone 6.2 — Inventory API with a SQLite Repository [mid]

> Rebuild the Orders pattern for warehouse inventory — parts, stock levels, reservations — with *both* repositories (in-memory and SQLite) behind one protocol, selected by `pydantic-settings`, and a readiness probe that actually exercises the database.

## Objective

A settings-driven FastAPI inventory service where the same test suite passes
against the in-memory and SQLite backends with zero code changes.
Reservation is a *domain transition* with invariants mapped to 409, and
`/ready` fails when the database file is unreadable.

## Inputs/Datasets

- A generated fixture of 500 synthetic parts (`NWR-0001`…`NWR-0500`) with
  stock counts; 1% deliberately invalid rows for negative tests.
- Reference fixtures: `..\..\datasets\northwind_robotics\parts.csv`,
  `..\..\datasets\northwind_robotics\inventory.csv`.

## Steps

1. Model `Part`, `Reservation`, and their create/read counterparts.
2. Implement both repositories; the SQLite one creates its schema
   idempotently.
3. Implement reservation as a domain transition with invariants (cannot
   reserve more than on-hand; cannot cancel a shipped reservation) mapped
   to 409 with a problem document.
4. Make `/ready` fail when the database file is unreadable.
5. Test both backends through the factory seam.

## Acceptance Criteria

- [ ] The same suite passes against `memory` and `sqlite` settings with
      zero code changes.
- [ ] Oversubscribing a part returns 409 with a problem document naming the
      part and the shortfall.
- [ ] Readiness returns 503 when the SQLite path is a directory (probing
      the failure path, not mocking it).

## Stretch Goals

- Optimistic concurrency: a `version` field checked on update (412
  Precondition Failed on mismatch; Chapter 10 generalizes).

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
