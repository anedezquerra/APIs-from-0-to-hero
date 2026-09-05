# Capstone 10.1 — Idempotency-Key Client SDK [junior]

> Build the client half of the idempotency protocol: a small Python class wrapping `httpx` that mints one key per logical operation and replays it across retries, speaking to the chapter's idempotent transfer server.

## Objective

Prove exactly-once *effect* over an at-least-once network: one `Operation`
mints one UUIDv4 key, retries bounded on connection errors and 409 (honoring
`Retry-After`), never retries 422, and a tampered payload under the same key
surfaces the server's 422 to the caller.

## Inputs/Datasets

- The chapter's Listing 10.1 idempotent transfer server (offline; stub or
  MockTransport in tests).
- The Northwind Robotics transfer payload fixture from the chapter's test
  suite; reference data: `..\..\datasets\northwind_robotics\orders.csv`.

## Steps

1. Implement `Operation` objects that mint a UUIDv4 key at construction.
2. Implement `submit()` with bounded retry: retry on connection error and
   on 409 (honoring `Retry-After`), never on 422.
3. Prove a retried submit yields exactly one ledger entry.
4. Prove a tampered payload under the same key surfaces the 422.
5. Log every attempt with attempt number and outcome.

## Acceptance Criteria

- [ ] One `Operation` retries up to 5 times and produces exactly one
      server-side mutation.
- [ ] 422 is never retried; 409 is retried with backoff.
- [ ] A second `Operation` mints a fresh key and executes a second
      transfer.
- [ ] All tests pass offline and deterministically.

## Stretch Goals

- Persist in-flight operations to a local file so a crashed client resumes
  with the same key.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
