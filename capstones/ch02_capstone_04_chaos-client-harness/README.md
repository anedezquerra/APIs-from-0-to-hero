# Capstone 2.4 — Chaos-Client Harness [senior]

> Build a fault-injection transport between your resilient client and the stub, and prove empirically that the resilience policy works: the client survives a gauntlet of injected faults with predictable behavior.

## Objective

Implement a `ChaosTransport` wrapping `httpx.MockTransport` with a scripted,
seeded fault schedule, define the expected client behavior per fault as an
executable contract, and run the full SDK against each schedule — asserting
both outcomes *and* bounds (total attempts, total sleep, bytes buffered).

## Inputs/Datasets

- A fault schedule (YAML or JSON): connect resets, read stalls, truncation,
  500 bursts, 429s with/without `Retry-After`, gigantic `Content-Length`
  lies, and capped synthetic gzip bombs.
- The Capstone 2.3 SDK (or the chapter's resilient client) as the system
  under test.

## Steps

1. Implement `ChaosTransport(BaseTransport)` reading a JSON fault schedule;
   deterministic via seeded RNG.
2. Define the expected behavior per fault (recover / fail-fast with typed
   error / abort with bounded time) as an executable contract.
3. Run the full SDK against each schedule; assert outcome *and* bounds:
   total attempts, total sleep, bytes buffered.
4. Produce a coverage report mapping faults → observed client behavior.

## Acceptance Criteria

- [ ] ≥ 8 distinct fault classes, each with an executable expectation.
- [ ] Every run reproducible from its seed; no wall-clock dependence.
- [ ] At least one fault deliberately exceeds the retry budget and the
      client demonstrably fails fast with the correct typed error.
- [ ] The decompression-bomb test proves the streaming path's size guard
      engages.

## Stretch Goals

- Latency distributions (injected p99 spikes) with a fake clock.
- Chaos schedules replayed from recorded (synthetic) production incident
  timelines.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
