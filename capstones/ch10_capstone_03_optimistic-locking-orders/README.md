# Capstone 10.3 — Optimistic-Locking Order Service [mid]

> Extend the chapter's stock listing into an order-reservation service in which reserving stock and releasing stock are both conditional writes, with a client that performs the read–decide–write–retry loop.

## Objective

Prove no lost updates under contention: reservations are quantity
transitions guarded by `If-Match` etags; the client retries bounded with
seeded jitter; 100 concurrent workers driven by a seeded script; global
conservation holds exactly.

## Inputs/Datasets

- The chapter's Listing 10.3 ETag-guarded stock service.
- A seeded catalog of 10 SKUs; a deterministic order script (seeded random
  choice of SKU and quantity).
- Reference fixture: `..\..\datasets\northwind_robotics\inventory.csv`.

## Steps

1. Model reservations as quantity transitions guarded by `If-Match`.
2. Implement the client retry loop with bounded attempts and deterministic
   (seeded) jitter.
3. Drive 100 concurrent order workers from the seeded script.
4. Assert global conservation: final quantity equals initial minus sum of
   accepted reservations.
5. Emit a contention report: attempts histogram, 412 rate per SKU.

## Acceptance Criteria

- [ ] No lost updates under the 100-worker storm (conservation invariant
      holds exactly).
- [ ] Blind writes receive 428; stale writes receive 412.
- [ ] The contention report is identical across runs.

## Stretch Goals

- Adaptive escalation: SKUs whose 412 rate exceeds a threshold switch to a
  serialized per-SKU queue; show the throughput/latency trade-off in the
  report.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
