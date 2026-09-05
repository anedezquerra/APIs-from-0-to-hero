# Capstone 16.1 — BOLA Hunter [junior]

> Build a small FastAPI notes API (`GET/PATCH /notes/{id}`) with an ownership model, then write an exploit script and the fix.

## Objective

See Broken Object Level Authorization from both sides: a vulnerable build
whose `GET /notes/{id}` lacks the ownership check falls to a 20-line
enumeration script; the hardened build answers 403 for every cross-owner
access, with a regression test that keeps it closed.

## Inputs/Datasets

- A synthetic in-memory store of 20 notes owned by 4 fictional users.
- Unsigned-lab tokens are acceptable here (this capstone predates the JWT
  requirement).

## Steps

1. Implement the API with the ownership check deliberately missing on
   `GET`.
2. Write `exploit.py` that enumerates ids 1–20 with one user's credential
   and dumps every note.
3. Add the `Guard`-style object check.
4. Re-run: the exploit must now produce 20 denials.
5. Add a regression test asserting the 403.

## Acceptance Criteria

- [ ] Exploit script retrieves a foreign note against the vulnerable build.
- [ ] Hardened build answers 403 for every cross-owner access.
- [ ] Pytest suite asserts both exploit-succeeds and fix-holds, all offline.
- [ ] README explains why unguessable ids alone would not fix it.

## Stretch Goals

- Add `ETag`-based conditional writes (Chapter 10).
- Make ids UUIDv7 and show the enumeration script fail — then explain why
  that is not the control.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
python starter.py --dry-run
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
