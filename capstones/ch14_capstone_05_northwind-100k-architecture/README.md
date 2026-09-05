# Capstone 14.5 — Rate-Limiting Architecture for Northwind at 100k rps [staff]

> Produce the complete design document for rate limiting, quotas, and shedding across Northwind Robotics' public API surface at 10⁵ rps in five regions.

## Objective

A staff-grade design document, backed by executable checks: endpoint tier
classification, per-tier topology with latency budgets, the header contract
and quota endpoints, a failure runbook for the three named incidents, and a
cost model showing limiter infrastructure under 2% of serving cost.

## Inputs/Datasets

- This chapter.
- A synthetic endpoint inventory you author (40 endpoints across
  read/write/export/admin classes with measured cost weights).
- A synthetic tenant registry (3 tiers, 2,000 tenants, one known-abusive
  actor).

## Steps

1. Classify every endpoint into a protection tier (exactness-required,
   approximate-fair, shedding-only) and defend each classification.
2. Choose the topology per tier (global cell / regional / local-plus-sync)
   with latency budgets; justify the 1 ms hot-path budget's consequences.
3. Specify the header contract, quota endpoints, and the policy-versioning
   story.
4. Write the failure runbook: limiter-cell outage, abusive-tenant drill,
   capacity-brownout (AIMD kick-in), including the fail-open/fail-closed
   assignment per tier.
5. Model cost: Redis cell sizing from key cardinality and N, and the egress
   cost of rejecting cheaply versus serving slowly.
6. Red-team your own design with the chapter's case-study playbook.

## Acceptance Criteria

- [ ] Every endpoint has a tier, a topology, a failure policy, and a
      numeric limit with a derivation (not a round number from nowhere).
- [ ] Over-admission bounds are stated and monitored per approximate tier.
- [ ] Runbook covers the three named incidents with detection signals and
      rollback steps.
- [ ] Cost model shows limiter infrastructure < 2% of serving cost at
      10⁵ rps, or explains why not.
- [ ] Red-team section names at least two residual weaknesses honestly.

## Stretch Goals

- Specify the GraphQL cost-scoring integration and the gRPC interceptor
  analogue so all three protocol surfaces share one budget.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
python starter.py --dry-run   # prints the design-doc outline
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
