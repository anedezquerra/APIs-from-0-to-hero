# Capstone 18.5 — Incident Program in a Box [staff]

> Stand up the complete operational loop for the fleet-telemetry platform and run a game day against it.

## Objective

The whole SRE loop, reproducible from seeds: SLOs (availability + latency +
freshness) for three services, runbooks generated and filled for all three,
the chapter's retry-storm case study scripted into the simulator, a two-role
game day with measured detection/mitigation/resolution times, and a
blameless postmortem with at least one alerting-topology change.

## Inputs/Datasets

- The chapter's Listings 18.3–18.6 (metrics, alerts, runbook/postmortem
  generators).
- The chapter's case study as the game-day scenario.
- Reference fixture: `..\..\datasets\northwind_robotics\telemetry_events.jsonl`.

## Steps

1. Define SLOs (availability + latency + freshness) for three services with
   per-endpoint thresholds.
2. Generate runbooks from the chapter's generator for all three services
   and fill every placeholder.
3. Script the retry-storm incident into the simulator's timeline plus a
   fan-out metric; verify the fast/slow pages and show that a
   spans-per-trace alert fires *before* the latency burn pages.
4. Run the game day: one teammate injects the fault, another follows only
   the runbook; measure detection, mitigation, and resolution times.
5. Produce the blameless postmortem from the generator, including the
   "lessons for the SLO" section with at least one concrete alerting change.

## Acceptance Criteria

- [ ] SLOs, runbooks, and dashboards-as-tables exist for all three services
      and cite one another.
- [ ] The game day produces measured detection/mitigation/resolution times,
      all reproducible from seeds.
- [ ] The postmortem is complete, blameless, and its action items include
      one alerting-topology change with an owner.
- [ ] A second run by a different pair reproduces the timelines within one
      minute of simulated time.

## Stretch Goals

- A budget-policy gate: when the simulator shows > 75% budget consumed, the
  deploy script refuses to ship and explains why.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
