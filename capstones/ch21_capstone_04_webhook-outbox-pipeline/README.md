# Capstone 21.4 — Webhook Notification Pipeline with Outbox Replay [senior]

> Implement the partner-notification subsystem of the reference architecture end to end.

## Objective

Outbox table + polling relay with exponential backoff, HMAC-signed webhooks
verified at a receiving endpoint you also build (with replay protection via
timestamp windows), a persisted delivery log with attempt counts, a
`POST /v1/webhooks/{id}/replay` endpoint, AsyncAPI documentation under the
conformance checker, and an SSE fallback stream carrying the same events.

## Inputs/Datasets

- The async-chapter outbox pattern.
- A synthetic partner endpoint (a local FastAPI receiver you also build).
- Reference fixture: `..\..\datasets\northwind_robotics\orders.csv`
  (`order.created`, `order.shipped` events).

## Steps

1. Add an outbox table and relay loop to the platform skeleton (in-process,
   polling, with exponential backoff).
2. Sign every webhook with HMAC; build the receiving endpoint to verify
   signatures and reject replays outside a timestamp window.
3. Persist a delivery log with attempt counts and last error; expose
   `POST /v1/webhooks/{id}/replay`.
4. Emit AsyncAPI documentation for the event catalog; extend the
   conformance checker's A-001 to cover it.
5. Add an SSE fallback stream carrying the same events for partners who
   cannot receive inbound webhooks.

## Acceptance Criteria

- [ ] No event is lost across a simulated broker/receiver outage (a test
      proves it).
- [ ] Signature failures and stale timestamps are rejected with 401/422
      problem details.
- [ ] Replay re-sends exactly the logged event payload.
- [ ] AsyncAPI spec passes the conformance checker.

## Stretch Goals

- Dead-letter queue with operator triage endpoint.
- Delivery-latency histogram exported as an OTel-style metric.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
