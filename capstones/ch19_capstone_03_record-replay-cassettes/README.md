# Capstone 19.3 — Record–Replay Cassette Library [mid]

> Build a minimal VCR for `httpx` and learn where cassettes rot.

## Objective

A recording transport that writes cassettes and a replaying transport that
serves them, with sanitization hooks so no credential-like header ever
reaches disk — plus a freshness check, demonstrated by mutating the app and
showing replay alone cannot detect the drift.

## Inputs/Datasets

- The chapter's `code\ch19\` robot registry.
- A JSON cassette format you design (request key → recorded
  status/headers/body).

## Steps

1. Implement a recording transport that writes cassettes and a replaying
   transport that serves them.
2. Add sanitization hooks (strip `Authorization`, redact fields).
3. Record the robot-registry interactions; replay with the app offline.
4. Mutate the app (change a field) and demonstrate that replay cannot
   detect it — then add a cassette "freshness date" check.

## Acceptance Criteria

- [ ] Replay works with zero application code.
- [ ] No credential-like header ever reaches disk.
- [ ] A stale cassette is detected and reported by date or hash.

## Stretch Goals

- Request matching on method+path+canonical body; strict versus lax
  matching modes.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
