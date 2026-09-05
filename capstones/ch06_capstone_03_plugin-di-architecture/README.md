# Capstone 6.3 — Plugin-Style Dependency-Injection Architecture [senior]

> Refactor the Orders API so that *repositories, notifiers, and pricing policies are plugins*: implementations register themselves in a module-level registry, settings select them by name, and the lifespan composes the chosen set — with a test suite that swaps each plugin via `dependency_overrides` without touching route code.

## Objective

A plugin architecture done with registry + settings + lifespan composition:
adding a plugin touches exactly one new file plus one registry line; unknown
plugin names fail fast at startup; every plugin is replaceable per test.

## Inputs/Datasets

- The chapter's Orders API as the base.
- Two synthetic notifier plugins ("webhook-log" and "audit-ndjson") and two
  pricing policies ("list" and "fleet-discount").
- Reference fixtures: `..\..\datasets\northwind_robotics\orders.csv`,
  `..\..\datasets\northwind_robotics\order_lines.csv`.

## Steps

1. Define protocols for `Notifier` and `PricingPolicy`.
2. Build a registry (name → factory) with fail-fast errors on unknown
   names.
3. Extend `Settings` with `notifier: str` and `pricing: str`; the lifespan
   instantiates the selection.
4. Thread both through DI into the order lifecycle (price on create, notify
   on status change).
5. Prove isolation: each plugin has tests using overrides, and one test
   boots every registry entry.

## Acceptance Criteria

- [ ] Adding a new plugin touches exactly one new file plus one registry
      line — no route or factory edits.
- [ ] Booting with `NWR_NOTIFIER=bogus` fails at startup with an actionable
      error, not at first request.
- [ ] Override tests demonstrate that notifications and pricing are
      replaceable per test, per request graph.

## Stretch Goals

- Emit the effective plugin set and versions into `/health` and a startup
  log line.
- A contract test that every registered notifier satisfies the protocol
  against a shared behavioral suite.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
