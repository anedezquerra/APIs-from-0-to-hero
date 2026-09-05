# Capstone 21.2 — Governance Toolchain [mid]

> Grow the chapter's conformance checker into a team-grade lint gate.

## Objective

Extend the conformance checker with three new rule families, dual
console/JSON reporting with stable rule codes, a `--fix-hints` mode, and a
changed-only CI mode that fails on violations in the candidate spec folder
while ignoring pre-existing violations in untouched files.

## Inputs/Datasets

- `conformance_checker.py` and both fixture folders from the chapter.
- The invariants of the lifecycle/governance chapter.

## Steps

1. Add three new rules: every operation has a camelCase `operationId`;
   every error schema is registered in `components`, not inlined; AsyncAPI
   channel names follow `domain.noun.verb`.
2. Produce both a console report and a machine-readable JSON report with
   stable rule codes.
3. Add a `--fix-hints` mode that prints the smallest suggested remediation
   per violation.
4. Wire the checker into a script that fails CI on any violation in a
   changed spec only (accept a folder pair: baseline vs. candidate).

## Acceptance Criteria

- [ ] All five original rule families plus the three new rules fire on
      `fixtures_fail` and pass on `fixtures_pass`.
- [ ] JSON report parses and round-trips deterministically.
- [ ] Changed-only mode ignores pre-existing violations in untouched files.
- [ ] Tests cover each new rule with a positive and negative fixture.

## Stretch Goals

- Severity levels (error/warning) with per-rule overrides in a policy file.
- SARIF output for code-scanning integration.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
python starter.py --baseline fixtures_pass --candidate fixtures_fail
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
