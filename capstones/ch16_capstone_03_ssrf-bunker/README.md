# Capstone 16.3 — SSRF Bunker [mid]

> Harden a "webhook tester" feature against SSRF with the full seven-layer gauntlet and a simulated adversary network.

## Objective

Build the naive fetcher, exploit it three ways (metadata IP, internal host,
redirect chain), then layer in the `SafeFetcher` policy one control at a
time — re-running the exploits after each — until all are blocked, with a
layer-by-layer blame table in the README.

## Inputs/Datasets

- The chapter's `fake_network.py` plus two hosts you add: one that
  redirects twice into link-local space, one serving a 1 MB body.

## Steps

1. Build the naive fetcher and exploit it three ways (metadata IP,
   internal host, redirect chain).
2. Layer in the `SafeFetcher` policy one control at a time, re-running
   exploits after each.
3. Add DNS-pinning and redirect re-validation tests.
4. Document which layer stops which exploit — including the layers that
   stop *nothing* alone but matter in composition.

## Acceptance Criteria

- [ ] All naive exploits succeed pre-fix, all blocked post-fix,
      demonstrated in one pytest run.
- [ ] DNS-rebinding and redirect tests included.
- [ ] A layer-by-layer blame table in the README.

## Stretch Goals

- IPv6-mapped IPv4 bypass attempts.
- Egress-rule simulation as a second, independent transport wrapper.

## Setup & Run (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

## Grading

See the book's **Appendix: Solutions & Grading Rubrics**.
