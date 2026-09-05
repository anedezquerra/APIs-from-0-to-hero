# Capstone 10.5 — Correctness Audit of a Retry-Capable Gateway [staff]

> Design and execute a full duplicate-safety audit for a fictitious API platform: enumerate every retry source (client SDK, proxy, load balancer, queue redelivery), classify every mutation endpoint by idempotency posture, and produce the remediation plan.

## Objective

Author a synthetic platform registry (20 endpoints with methods, retry
sources, and current dedup posture), write a linter that flags unprotected
unsafe methods reachable by any retry source, and specify fixes with
enforcement mechanisms — not just headers — plus the ongoing telemetry and
alert thresholds that would have caught the chapter's war story.

## Inputs/Datasets

- A synthetic platform registry you author (YAML: 20 endpoints with
  methods, retry sources, current dedup posture) — include seeded violations
  the linter must flag.
- The chapter's Listings 10.1–10.5 as the reference implementation kit.

## Steps

1. Build the retry-source inventory: for each endpoint, list every layer
   that can duplicate a request.
2. Classify endpoints: spec-idempotent, key-protected, unprotected.
3. Write a linter that flags unprotected unsafe methods reachable by any
   retry source.
4. For the top three risk endpoints, specify the fix (key protocol
   adoption, PUT redesign, or constraint-backed dedup) with migration steps.
5. Define the ongoing telemetry: replay rate, 409 rate, 422 rate, and the
   alert thresholds that would have caught the chapter's war story.

## Acceptance Criteria

- [ ] The registry linter flags exactly the seeded violations, with zero
      false positives on the protected endpoints.
- [ ] Every remediation references the mechanism that enforces it (unique
      constraint, fingerprint, fencing token) — not just a header.
- [ ] The telemetry plan includes at least one alert tied to each failure
      mode in the war story.
- [ ] The plan states the blast radius of the idempotency-key store being
      unavailable and how the platform degrades.

## Stretch Goals

- Extend the audit across the async boundary: model queue redelivery for
  each endpoint's emitted events and specify consumer-side dedup windows.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
