# Capstone 10.4 — Cache-Policy Workbench [senior]

> Turn the chapter's cache simulator into a policy evaluation tool: given a traffic timeline and a library of candidate policies, rank them by origin load, staleness window, and error resilience.

## Objective

A deterministic simulator that replays a synthetic one-hour request timeline
(arrivals, origin mutation events, one scripted outage) against five
candidate cache policies from `no-store` to `max-age=300,
stale-while-revalidate=60, stale-if-error=600`, and produces a comparison
table plus a one-page recommendation memo.

## Inputs/Datasets

- The chapter's Listing 10.5 simulator core.
- A JSON fixture: the one-hour timeline plus the five candidate policies.
- Reference fixture: `..\..\datasets\northwind_robotics\api_access_log.jsonl`
  as a model for request-arrival shapes.

## Steps

1. Load timelines and policies from a JSON fixture.
2. Simulate every (policy, timeline) pair.
3. Produce a comparison table: origin fetches, bytes saved, longest stale
   serve, requests failed during the outage.
4. Write a one-page recommendation memo choosing a policy per surface
   (product page, pricing API, account page).
5. Add a regression test asserting the ranking is stable.

## Acceptance Criteria

- [ ] The table is reproducible bit-for-bit from the fixtures.
- [ ] At least one policy is shown to serve zero failed requests during the
      scripted outage, and the memo explains why.
- [ ] The account page is assigned `no-store` or `private` with a
      one-sentence justification.

## Stretch Goals

- Model a shared cache with a `Vary` dimension and demonstrate a
  misconfiguration that leaks across user segments.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
