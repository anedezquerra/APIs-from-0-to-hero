# Capstone 6.5 — OpenAPI-First Generator Round-Trip [staff]

> Close the design-first loop: author `orders.openapi.yaml` by hand for a superset of the chapter's API (adding shipments), generate a FastAPI skeleton and a typed Python client from it, implement the skeleton, and build a CI-style gate that fails when the running app's schema diverges from the authored contract — then perform a governed contract change end to end.

## Objective

Prove you can run a contract-first workflow: the authored spec is the
source of truth; the running service must round-trip against it with zero
diffs; a diff gate classifies every change as breaking or compatible with
human-readable reasons.

## Inputs/Datasets

- The authored spec (`orders.openapi.yaml`, OpenAPI 3.1).
- The chapter's Orders API as the seed implementation.
- Two "change requests": an optional `priority` field on orders
  (backward compatible) and a field rename (breaking).
- Reference fixtures: `..\..\datasets\northwind_robotics\orders.csv`,
  `..\..\datasets\northwind_robotics\customers.csv`.

## Steps

1. Author the 3.1 spec with `servers`, `components`, `securitySchemes`,
   and complete error responses.
2. Generate or hand-synthesize the skeleton from the spec; implement
   against it.
3. Implement the diff gate: fetch `/openapi.json`, compare against the
   pinned spec, classify every difference as breaking or compatible.
4. Apply the compatible change: spec first, code second, gate green.
5. Attempt the breaking change and document how the gate stops it.

## Acceptance Criteria

- [ ] The gate classifies the seeded compatible and breaking changes
      correctly, with human-readable reasons.
- [ ] The running service passes its own gate; pinned spec and generated
      schema round-trip with zero diffs.
- [ ] The typed client consumes the service in a TestClient integration
      test with no hand-edited models.
- [ ] A written policy states who may bump which version number and when.

## Stretch Goals

- Emit the diff report as an RFC 9457 problem document.
- Extend the gate to detect *undocumented* endpoints (in code, absent from
  spec) as a distinct violation class.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
