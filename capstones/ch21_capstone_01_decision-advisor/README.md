# Capstone 21.1 — Extend the Decision Advisor [junior]

> Deepen the chapter's protocol decision advisor into a usable team tool.

## Objective

Turn the advisor listing into a team-grade CLI: an interactive
questionnaire over the six decision criteria, a seventh criterion
(data residency), and an `--explain` flag printing the full score table —
all with rationale traces and no regression to existing winners.

## Inputs/Datasets

- `protocol_advisor.py` and its test file from the chapter.
- The chapter's decision-criteria table.

## Steps

1. Add an interactive questionnaire mode that prompts for the six criteria
   and prints the recommendation with its rationale trace.
2. Add a seventh criterion (data-residency constraint) with signals that
   penalize public-CDN-dependent profiles when residency forbids edge
   caching.
3. Add a `--explain` flag that prints the full score table for all five
   profiles, not only the winner.
4. Extend the tests: the new criterion must change at least one canonical
   scenario's runner-up margin without flipping any existing winner.

## Acceptance Criteria

- [ ] Questionnaire mode runs offline and rejects invalid answers with a
      clear message.
- [ ] All pre-existing advisor tests pass unmodified.
- [ ] New tests cover the residency criterion and `--explain` output.
- [ ] Rationale traces mention the residency criterion when it moved a
      score.

## Stretch Goals

- Emit the score table as JSON for CI consumption.
- A "confidence" metric based on the winner's margin.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
python starter.py --explain
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
