# Capstone 16.2 — Scope Forge & Token Gauntlet [mid]

> Stand up a toy resource server with the full token-validation pipeline and a scope model, then attack it with a forgery battery.

## Objective

Design a coarse/fine scope vocabulary for a three-resource fleet domain,
wire the chapter's validator into three endpoints with different required
scopes, and prove the pipeline holds against seven forgeries — with
`WWW-Authenticate` diagnostics on every failure.

## Inputs/Datasets

- The chapter's `jwks_fixture.py` and `token_validation.py` (synthetic keys).
- A scope vocabulary you design for a three-resource fleet domain.

## Steps

1. Design coarse/fine scope sets; document the trade-off.
2. Wire the validator into three endpoints with different required scopes.
3. Write adversarial tests: expired, wrong `aud`, wrong `iss`, `alg=none`,
   unknown `kid`, tampered payload, missing scope.
4. Add `WWW-Authenticate` diagnostics on failures.

## Acceptance Criteria

- [ ] Seven forgery tests all produce 401/403, none 200.
- [ ] Validation order provably never reads claims before signature
      verification (test with an unsigned token carrying admin claims).
- [ ] Scope design document justifies each scope's granularity.

## Stretch Goals

- Token exchange to a second "service" with narrowed scope and audience.
- Clock-skew boundary tests.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
