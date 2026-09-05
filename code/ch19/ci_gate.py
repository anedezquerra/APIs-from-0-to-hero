"""CI quality gate: contract verify + fuzz smoke + perf smoke -> exit code.

Each sub-gate returns (passed, detail). The contract and fuzz gates include
a *self-check*: they also run against a deliberately broken variant and
require that the gate catches it -- a gate that cannot fail is not a gate.

Run:  python ci_gate.py        (exit code 0 = PASS, 1 = FAIL)
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx

from fuzz_openapi_mini import REQUEST_SCHEMA, fuzz_cases, run_fuzz
from load_harness import create_workload_app, open_loop
from pact_mini import PROVIDER_STATES, ProviderVerifier, record_demo_pact
from robot_registry import create_app, make_sync_client

PACT_DIR = Path(__file__).resolve().parent / "pacts"


def contract_gate() -> tuple[bool, str]:
    pact = record_demo_pact(PACT_DIR)
    healthy = ProviderVerifier(create_app, pact, PROVIDER_STATES).verify()
    broken = ProviderVerifier(lambda: create_app(breaking=True), pact, PROVIDER_STATES).verify()
    detail = (
        f"{len(healthy.results)} interactions, {len(healthy.failures())} mismatches; "
        f"self-check: breaking variant rejected with "
        f"{len(broken.failures())} mismatch(es)"
    )
    return healthy.ok and not broken.ok, detail


def fuzz_gate() -> tuple[bool, str]:
    cases = fuzz_cases(REQUEST_SCHEMA)
    healthy_client = make_sync_client(create_app(), base_url="http://gate.test")
    total, failures = run_fuzz(healthy_client, cases)
    buggy_client = make_sync_client(create_app(bug_at_price=666), base_url="http://gate.test")
    _, self_check_failures = run_fuzz(buggy_client, cases)
    detail = (
        f"{total} cases, {len(failures)} failures; "
        f"self-check: planted bug found ({len(self_check_failures)} failing case(s))"
    )
    return not failures and bool(self_check_failures), detail


def perf_gate() -> tuple[bool, str]:
    """Perf smoke: short open-model burst. Asserts *structure* (all scheduled
    requests completed, zero 5xx), never wall-clock latency thresholds."""

    async def burst() -> tuple[int, int]:
        app = create_workload_app()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://gate.test"
        ) as client:
            hist = await open_loop(client, rps=50, duration_s=0.4)
        return hist.total, hist.errors

    total, errors = asyncio.run(burst())
    expected = int(50 * 0.4)  # deterministic scheduled count modulo float edge
    ok = errors == 0 and abs(total - expected) <= 1
    return ok, f"{total} requests (~{expected} scheduled), {errors} server errors"


GATES = (
    ("contract verify", contract_gate),
    ("fuzz smoke", fuzz_gate),
    ("perf smoke", perf_gate),
)


def main() -> int:
    print("== API quality gate ==")
    all_ok = True
    for name, gate in GATES:
        try:
            passed, detail = gate()
        except Exception as exc:  # a crashing gate is a failing gate
            passed, detail = False, f"gate crashed: {exc!r}"
        all_ok &= passed
        print(f"[{'PASS' if passed else 'FAIL'}] {name:<16} {detail}")
    print(f"GATE RESULT: {'PASS' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
