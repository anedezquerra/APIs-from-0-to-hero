# Capstone 18.4 — Queue Propagation End to End [senior]

> Close the tracing gap the chapter warns about: one trace across HTTP *and* a message broker.

## Objective

Trace context through an in-process fake broker: the gateway injects
`traceparent`/`tracestate` into message metadata, a consumer extracts
context and starts a correctly parented `CONSUMER` span, a batch consumer
uses span links for its 50 parents, and a legacy consumer that drops unknown
metadata produces a *detectably* orphaned span.

## Inputs/Datasets

- The chapter's Listing 18.3 (tracing pipeline).
- An in-process fake broker you write (dict of queues; no network,
  deterministic).

## Steps

1. Publish telemetry from the gateway to the fake broker, injecting
   `traceparent`/`tracestate` into message metadata.
2. A consumer extracts context and starts a `CONSUMER` span parented
   correctly; a batch consumer uses span links for its 50 parents.
3. Export and assert: one trace id spans HTTP ingress, publish, and
   consume; batch consumption produces one span with 50 links.
4. Write the failure-mode test: a legacy consumer that drops unknown
   metadata fields produces a detectably orphaned span (assert and log a
   warning).

## Acceptance Criteria

- [ ] The exported tree crosses the broker boundary with one trace id and
      correct parentage.
- [ ] Batch consumption uses links, not a false single parent.
- [ ] The legacy-consumer test detects the orphaned span programmatically.

## Stretch Goals

- A redaction pass that strips baggage at the queue boundary; prove no
  baggage key survives into consumer spans.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
