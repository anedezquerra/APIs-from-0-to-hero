# Capstone 2.1 — Robust CLI Downloader [junior]

> Build `nrget`: a PowerShell-friendly CLI that downloads a part's datasheet (`/catalog/export`) from the local stub to a local file — correctly and observably.

## Objective

Build a small command-line downloader around `httpx.Client` that streams the
Northwind catalog export to disk. It must be correct under failure (no
partial artifacts), observable (structured progress logging, no header
leakage), and explicit about time (every call carries four-dimension
timeouts). Exit codes are part of the contract.

## Inputs/Datasets

- The chapter's local stub `/catalog/export` endpoint (synthetic Northwind
  catalog, NDJSON). Tests must pass with the stub stopped, using
  `httpx.MockTransport`.
- Reference fixture: `..\..\datasets\northwind_robotics\parts.csv`.

## Steps

1. Wrap `httpx.Client` with explicit connect/read/write/pool timeouts and a
   typed error taxonomy (`DownloadError` → `ClientError`, `ServerError`).
2. Stream the body with `iter_bytes`, writing to a `.part` temp file and
   atomically renaming it on success.
3. Print byte-level progress to the console; support a `--max-bytes` guard.
4. Exit codes: `0` success, `2` client error, `3` server/transient error
   after bounded retries.

## Acceptance Criteria

- [ ] No call lacks an explicit timeout (verified by inspection plus a test
      asserting the client's timeout fields).
- [ ] A killed/failed download leaves no partial artifact (no stray `.part`
      or truncated target file).
- [ ] MockTransport tests cover 200, 404, 500-then-200, and malformed-body
      paths; the suite passes with the stub stopped.
- [ ] Logs contain method/path/status/latency and **no** headers.

## Stretch Goals

- Resume support via `Range` requests.
- A `--dry-run` mode that prints the request plan without sending anything.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
python starter.py --help
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
