# Capstone 16.5 — Full Red Team / Blue Team Exercise [staff]

> Run a two-sided exercise on a multi-service Northwind Robotics topology: a red team exploits a seeded environment; a blue team ships fixes without breaking the contract test suite.

## Objective

Security work as executable evidence: at least ten seeded flaws across two
services (including one cross-service token-confusion flaw), every red
finding expressed as a failing contract test *before* it is shown, and a
blue team that closes them while the functional suite stays green.

## Inputs/Datasets

- The chapter's vulnerable app extended with a second service (billing), a
  JWKS fixture with two audiences, and the simulated network.
- A scoring rubric mapping findings to OWASP API Security Top 10 items.

## Steps

1. Seed at least ten flaws across both services, including one
   cross-service token-confusion flaw (billing tokens accepted by fleet).
2. Red team: document each exploit as a failing contract test before
   showing it.
3. Blue team: fix until the contract suite is green and the functional
   suite stays green.
4. Retro: map every finding to an OWASP item, a detection signal, and a
   control that would have prevented it by construction.

## Acceptance Criteria

- [ ] Every red finding exists as an executable contract test (no
      slide-deck-only findings).
- [ ] Cross-service audience-confusion exploit demonstrated and closed.
- [ ] Functional test suite remains green after hardening (security fixes
      must not break the contract).
- [ ] Retro document: findings → OWASP items → detection → permanent
      control.

## Stretch Goals

- mTLS between the two services via a local CA; show the token-confusion
  exploit's remaining path.
- Introduce a deliberate regression and measure time-to-detect with the new
  alerts.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
