# Capstone 16.4 — Threat-Model Pipeline [senior]

> Turn threat modeling into a build artifact: extend the chapter's STRIDE worksheet generator into a CI gate that fails when new endpoints ship without completed STRIDE rows.

## Objective

Threat modeling as code: skeletons are generated from the app's OpenAPI
document, humans complete the worksheets, and a `--check` mode diffs
generated skeletons against committed worksheets — red build on any
undocumented or unmodeled endpoint.

## Inputs/Datasets

- The hardened app's OpenAPI document.
- A completed worksheet file per endpoint, checked into the repo.

## Steps

1. Extend the generator with heuristics for query-string filters, file
   uploads, and webhook registrations.
2. Add a `--check` mode that diffs generated skeletons against committed,
   human-completed worksheets.
3. Wire it as a CI step; demonstrate a red build by adding an undocumented
   route.
4. Write two abuse cases with executable acceptance tests.

## Acceptance Criteria

- [ ] `--check` exits nonzero on undocumented or unmodeled endpoints, zero
      when worksheets are current.
- [ ] At least three new heuristics with unit tests.
- [ ] Two abuse cases expressed as passing security tests.

## Stretch Goals

- Emit attack-tree DOT files from the worksheet annotations.
- Score endpoint risk by flag count and data sensitivity.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
python starter.py --check
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
