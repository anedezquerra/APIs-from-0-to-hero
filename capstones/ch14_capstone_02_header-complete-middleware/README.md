# Capstone 14.2 — Header-Complete Middleware [mid]

> Extend the chapter's rate-limit middleware into middleware you would publish as a platform library.

## Objective

Production-shaped limiting middleware: a Redis-backed limiter behind the
`KeyedLimiter` protocol, complete IETF `RateLimit-*` headers, an
RFC 9457-style problem body on 429 (policy + documentation link), and an
explicit `X-NR-Limiter-Degraded: true` signal for fail-open episodes.

## Inputs/Datasets

- The chapter's Listings 14.1, 14.6, 14.7 (limiter, middleware, tests).
- The Northwind Robotics endpoint set: `/telemetry`, `/fleet/status`,
  `/reports/export`, `/health`.
- Reference fixture: `..\..\datasets\northwind_robotics\api_access_log.jsonl`.

## Steps

1. Swap the in-process limiter for the Redis limiter behind the
   `KeyedLimiter` protocol (add a `reset_after` implementation); use
   `fakeredis` offline.
2. Emit an RFC 9457-style problem body on 429, including the policy and a
   documentation link.
3. Add an `X-NR-Limiter-Degraded: true` signal for fail-open episodes
   (headers omitted, signal present).
4. Test: headers across a window boundary, problem body shape, degraded
   signal, and 401 versus 429 separation.

## Acceptance Criteria

- [ ] All of the chapter's middleware tests pass unmodified against the
      Redis-backed wiring.
- [ ] 429 bodies validate against a declared problem-details schema.
- [ ] Fail-open episodes emit the degraded signal and no `RateLimit-*`
      fields; fail-closed returns 503 + `Retry-After`.
- [ ] Full suite is deterministic and offline.

## Stretch Goals

- Per-plan policies (`"100;w=60"` vs. `"1000;w=60"`) selected by API-key
  tier.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
