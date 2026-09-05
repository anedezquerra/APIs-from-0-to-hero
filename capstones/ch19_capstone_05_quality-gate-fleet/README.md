# Capstone 19.5 — Quality-Gate Architecture for a Fleet [staff]

> Design the gate architecture for a (fictional) ten-service Northwind Robotics fleet.

## Objective

Allocate the test pyramid per service with a designated cheapest catcher per
defect class, specify the pact-broker topology, budget CI minutes per gate
with deep work moved to scheduled jobs, and write the flake policy plus the
advisory-to-blocking rollout plan for contract gates.

## Inputs/Datasets

- The chapter's gate architecture.
- A written fleet topology you invent (services, consumers, deploy
  cadences).

## Steps

1. Allocate pyramid layers per service with designated catchers per defect
   class.
2. Specify the broker topology: pact storage, version tagging,
   `can-i-deploy` semantics per environment.
3. Budget CI minutes per gate; move deep sweeps and soaks to scheduled jobs
   with archived evidence.
4. Write the flake policy (quarantine SLA, deletion rule, dashboards) and
   the advisory-to-blocking rollout plan for contract gates.

## Acceptance Criteria

- [ ] Every defect class in your taxonomy has exactly one designated
      cheapest catcher.
- [ ] The gate budget fits four minutes per PR with a written justification
      for each cut.
- [ ] The rollout plan includes measurable adoption metrics (pact coverage
      of production traffic) and a self-check requirement for every gate.

## Stretch Goals

- Mutation testing of the gates themselves (deliberately broken variants)
  as a scheduled meta-gate.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
python starter.py --dry-run   # prints the gate-architecture outline
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
