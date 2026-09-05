# Capstone 6.1 — Todo API with a Full Test Suite [junior]

> Build a minimal but *complete* FastAPI service: a todo-list API with create, read, list, complete, and delete operations, an in-memory repository behind a protocol, and a TestClient suite that covers every route.

## Objective

A small service done right: typed models with constraints, deterministic
IDs, `response_model` on every route, correct status codes (201/204/404/422),
and a test suite that proves the whole surface offline.

## Inputs/Datasets

- A seeded fixture of 20 synthetic todos (titles from the Northwind Robotics
  maintenance log, e.g. "recalibrate arm 7").
- Optional reference fixtures: `..\..\datasets\northwind_robotics\parts.csv`.

## Steps

1. Model `TodoCreate`/`TodoRead` with constraints (title 3–80 chars;
   `priority` 1–5).
2. Implement the repository protocol and an in-memory implementation with
   deterministic IDs.
3. Wire routes with `response_model` on all of them and correct status
   codes (201/204/404/422).
4. Write at least 10 tests: every happy path, a 404, and two distinct 422s.

## Acceptance Criteria

- [ ] `pytest -q` passes offline; IDs are deterministic per fresh app.
- [ ] Every route declares `response_model`; no internal field appears in
      any response body.
- [ ] The OpenAPI schema documents a 422 response for every route that
      accepts a body.

## Stretch Goals

- Add the correlation-ID middleware and assert the header echo.
- Add a `/todos-stream` NDJSON endpoint with a streaming test.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
