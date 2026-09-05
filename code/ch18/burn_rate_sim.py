"""Multi-window, multi-burn-rate SLO alerting simulator (offline, seeded).

Feeds a synthetic minute-by-minute traffic timeline for the Northwind
Robotics fleet API into the alerting logic from the Google SRE Workbook's
"Alerting on SLOs" chapter: an alert fires only when BOTH a long window
and a short window show a burn rate above the policy threshold.

    burn_rate(t, w)   = error_rate(t, w) / budget_rate
    budget_rate       = 1 - SLO                (0.001 for a 99.9% SLO)
    budget_consumed   = burn_rate * w / period (% of the 30-day budget)

Policy table (budget consumed if the burn persists for the long window):
    fast page  : burn 14.4  long 1h   short 5m   -> 2%  of budget
    slow page  : burn  6.0  long 6h   short 30m  -> 5%  of budget
    ticket     : burn  1.0  long 3d   short 6h   -> 10% of budget

Run:  python burn_rate_sim.py        (scripted incident demo)
      pytest burn_rate_sim.py -q     (embedded test suite)
"""

from __future__ import annotations

import random
from dataclasses import dataclass

SLO = 0.999
BUDGET_RATE = 1.0 - SLO              # 0.001
PERIOD_MINUTES = 30 * 24 * 60        # 30-day rolling window: 43,200 min
BUDGET_MINUTES_EQUIVALENT = BUDGET_RATE * PERIOD_MINUTES  # 43.2 min


@dataclass(frozen=True)
class MinuteSample:
    minute: int
    requests: int
    errors: int


@dataclass(frozen=True)
class BurnRatePolicy:
    name: str
    burn_rate: float
    long_window_min: int
    short_window_min: int

    @property
    def budget_consumed_pct(self) -> float:
        """% of the period budget burned if this rate lasts the long window."""
        return 100.0 * self.burn_rate * self.long_window_min / PERIOD_MINUTES


POLICIES = [
    BurnRatePolicy("fast-page", 14.4, 60, 5),
    BurnRatePolicy("slow-page", 6.0, 360, 30),
    BurnRatePolicy("ticket", 1.0, 3 * 24 * 60, 360),
]


@dataclass(frozen=True)
class Alert:
    policy: str
    fired_at: int
    long_burn: float
    short_burn: float


def window_rate(samples: list[MinuteSample], t: int, window: int) -> float:
    """Error rate over samples in (t - window, t]; 0.0 when no traffic."""
    total = errors = 0
    for s in samples:
        if t - window < s.minute <= t:
            total += s.requests
            errors += s.errors
    return errors / total if total else 0.0


def burn_rate(samples: list[MinuteSample], t: int, window: int) -> float:
    return window_rate(samples, t, window) / BUDGET_RATE


def _prefix_sums(samples: list[MinuteSample]) -> tuple[list[int], list[int]]:
    """Cumulative requests/errors per minute for O(1) window queries."""
    horizon = samples[-1].minute
    cum_req = [0] * (horizon + 1)
    cum_err = [0] * (horizon + 1)
    for s in samples:
        cum_req[s.minute] += s.requests
        cum_err[s.minute] += s.errors
    for t in range(1, horizon + 1):
        cum_req[t] += cum_req[t - 1]
        cum_err[t] += cum_err[t - 1]
    return cum_req, cum_err


def _burn(cum_req: list[int], cum_err: list[int], t: int, window: int) -> float:
    lo = max(0, t - window)  # window (t - window, t]
    total = cum_req[t] - cum_req[lo]
    errors = cum_err[t] - cum_err[lo]
    return (errors / total / BUDGET_RATE) if total else 0.0


def evaluate(
    samples: list[MinuteSample],
    policies: list[BurnRatePolicy] | None = None,
) -> list[Alert]:
    """First firing of each policy; reset requires the long window to clear."""
    fired: list[Alert] = []
    active: set[str] = set()
    if not samples:
        return fired
    policies = policies or POLICIES
    cum_req, cum_err = _prefix_sums(samples)
    for t in range(1, samples[-1].minute + 1):
        for policy in policies:
            if t < policy.long_window_min:
                continue  # window not yet fully populated; don't alert on cold data
            long_burn = _burn(cum_req, cum_err, t, policy.long_window_min)
            short_burn = _burn(cum_req, cum_err, t, policy.short_window_min)
            breached = (
                long_burn >= policy.burn_rate
                and short_burn >= policy.burn_rate
            )
            if breached and policy.name not in active:
                active.add(policy.name)
                fired.append(Alert(policy.name, t, long_burn, short_burn))
            elif long_burn < policy.burn_rate and policy.name in active:
                active.remove(policy.name)  # recovered; may re-fire later
    return fired


def synthetic_timeline(seed: int = 18, minutes: int = 3 * 24 * 60) -> list[MinuteSample]:
    """Three days of traffic; a scripted bad deploy burns hot for 50 minutes.

    Baseline: ~120 req/min with a healthy 0.05% error rate (below budget).
    Incident: minutes 2000..2049 at 8% errors --- an 80x burn rate, the
    classic "deploy wedged a dependency" shape. Everything seeded, so the
    alert timeline below reproduces on every machine.
    """
    rng = random.Random(seed)
    out: list[MinuteSample] = []
    for t in range(minutes):
        requests = 120 + rng.randint(-10, 10)
        error_rate = 0.08 if 2000 <= t < 2050 else 0.0005
        # errors are a deterministic quota plus seeded jitter around it
        errors = int(requests * error_rate) + (1 if rng.random() < 0.02 else 0)
        out.append(MinuteSample(t, requests, errors))
    return out


def _demo() -> None:
    samples = synthetic_timeline()
    print(f"timeline: {len(samples)} minutes, SLO={SLO}, "
          f"budget={BUDGET_MINUTES_EQUIVALENT:.1f} min-equivalent/30d")
    print(f"{'policy':<10} {'burn':>5} {'long':>6} {'short':>6} {'budget%':>8}")
    for p in POLICIES:
        print(f"{p.name:<10} {p.burn_rate:>5} {p.long_window_min:>5}m "
              f"{p.short_window_min:>5}m {p.budget_consumed_pct:>7.1f}%")
    print("\nalert timeline (minute = minutes since window start):")
    for alert in evaluate(samples):
        hh, mm = divmod(alert.fired_at, 60)
        print(f"  [t={alert.fired_at:>5} ({hh:02d}h{mm:02d}m)] PAGE {alert.policy}"
              f"  long-burn={alert.long_burn:.1f}x short-burn={alert.short_burn:.1f}x")


# ---------------------------------------------------------------------------
# Embedded test suite: pytest burn_rate_sim.py -q
# ---------------------------------------------------------------------------
def test_error_budget_minutes() -> None:
    assert abs(BUDGET_MINUTES_EQUIVALENT - 43.2) < 1e-9  # the famous 43.2 min/month


def test_budget_consumed_percentages_match_workbook_table() -> None:
    assert abs(POLICIES[0].budget_consumed_pct - 2.0) < 1e-9
    assert abs(POLICIES[1].budget_consumed_pct - 5.0) < 1e-9
    assert abs(POLICIES[2].budget_consumed_pct - 10.0) < 1e-9


def test_healthy_traffic_never_pages() -> None:
    samples = synthetic_timeline()
    healthy = [s for s in samples if not 1950 <= s.minute < 2100]
    assert evaluate(healthy) == []


def test_incident_fires_both_pages_but_no_ticket() -> None:
    alerts = evaluate(synthetic_timeline())
    fast = [a for a in alerts if a.policy == "fast-page"]
    assert fast, "an 80x burn for 50 minutes must page the fast policy"
    assert 2005 <= fast[0].fired_at <= 2060  # fires during/right after burst
    # 50 min at 80x still averages 11x over the 6h window -> slow page too
    assert any(a.policy == "slow-page" for a in alerts)
    # but 50 bad minutes out of 3 days stays under the 1x ticket threshold
    assert not any(a.policy == "ticket" for a in alerts)


def test_sustained_low_burn_fires_ticket_only() -> None:
    # 0.3% errors = 3x burn, sustained for the whole timeline
    samples = [
        MinuteSample(t, requests=1000, errors=3) for t in range(3 * 24 * 60 + 400)
    ]
    alerts = evaluate(samples)
    names = {a.policy for a in alerts}
    assert names == {"ticket"}, f"3x burn should page ticket only, got {names}"


def test_window_rate_excludes_boundary_and_handles_empty() -> None:
    samples = [MinuteSample(0, 100, 10), MinuteSample(5, 100, 0)]
    assert window_rate(samples, 5, 5) == 0.0            # (0, 5] holds minute 5 only
    assert window_rate(samples, 5, 6) == 10 / 200       # (-1, 5] holds both minutes
    assert window_rate(samples, 10, 5) == 0.0           # (5, 10] holds neither
    assert window_rate([], 10, 5) == 0.0


if __name__ == "__main__":
    _demo()
