# Capstone 18.1 — Trace Context Conformance Pack [junior]

> Prove you own the W3C trace-context wire format by extending the chapter's parser into a conformance checker.

## Objective

A data-driven conformance checker: a hand-written corpus of 20
`traceparent` headers (10 valid, 10 invalid in distinct ways) plus 5
`tracestate` headers, a runner that reports pass/fail per case,
forward-compatible parsing of version-`01` headers, and a 500-case seeded
round-trip property test.

## Inputs/Datasets

- The chapter's Listings 18.1–18.2 (parser).
- A hand-written corpus file of 20 `traceparent` headers (10 valid, 10
  invalid in distinct ways) plus 5 `tracestate` headers.

## Steps

1. Write the header corpus as a data file, one header per line with an
   expected verdict.
2. Build a checker that runs every corpus line through
   `parse_traceparent` and reports pass/fail per case.
3. Add version-`01` headers with trailing fields and verify
   forward-compatible parsing.
4. Add a property test: for 500 seeded random contexts,
   `parse(header(x)) == x`.

## Acceptance Criteria

- [ ] All 25 corpus cases produce the expected verdict.
- [ ] The seeded round-trip property test passes 500/500.
- [ ] Every rejection message names the offending field.

## Stretch Goals

- Fuzz with random truncations and case flips; assert the parser never
  throws anything but `ValueError`.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
