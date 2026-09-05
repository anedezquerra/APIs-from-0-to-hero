# Capstone 10.2 — Conditional-GET Sync Agent [junior]

> Write a catalog sync agent that polls the chapter's ETag-serving parts API on a fixed schedule and transfers bytes only when representations actually changed.

## Objective

Keep a local mirror of the parts catalog correct while moving almost no
bytes: per-SKU validator state (ETag + body) in a local JSON file,
`If-None-Match` on every poll, 304 = zero-byte sync, and a reproducible
savings report against a naive always-GET baseline.

## Inputs/Datasets

- The chapter's Listing 10.2 parts API (offline; MockTransport in tests).
- A scripted mutation schedule (restock events at chosen logical steps).
- Reference fixture: `..\..\datasets\northwind_robotics\parts.csv`.

## Steps

1. Keep per-SKU validator state (ETag + body) in a local JSON file.
2. On each poll, send `If-None-Match` when a validator exists.
3. On 304, keep the stored body and count a zero-byte sync; on 200, replace
   state.
4. Run 20 polls over the scripted schedule; report bytes transferred versus
   a naive always-GET baseline.
5. Prove a mid-run restock is observed exactly once.

## Acceptance Criteria

- [ ] 304 polls transfer zero representation bytes.
- [ ] The agent's local state always equals the server's current
      representation after each poll.
- [ ] The savings report is reproducible from the scripted schedule.

## Stretch Goals

- Add `Last-Modified`/`If-Modified-Since` as a fallback when no ETag is
  present.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
