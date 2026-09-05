"""Runbook and blameless-postmortem skeleton generator (stdlib only).

Incident response fails in predictable ways: nobody remembers the rollback
command at 3 a.m., and postmortems devolve into blame or vanish unwritten.
Both are structure problems, and structure is exactly what code is good at.
Given incident metadata, this module emits markdown skeletons with every
mandatory section present and every placeholder explicit, so the human
work is analysis, not formatting.

Run:  python incident_templates.py        (writes demo artifacts)
      pytest incident_templates.py -q     (embedded test suite)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

SEVERITIES = {
    "SEV1": "total outage or data loss; all-hands, page immediately",
    "SEV2": "major degradation of a core SLO; page the owning team",
    "SEV3": "minor degradation or single-tenant impact; ticket, next business day",
    "SEV4": "cosmetic or internal-only; backlog",
}


@dataclass(frozen=True)
class ServiceProfile:
    name: str
    slo_target: float
    owner: str
    endpoints: tuple[str, ...]
    dashboards: tuple[str, ...]
    rollback_command: str


@dataclass(frozen=True)
class IncidentMetadata:
    incident_id: str
    title: str
    severity: str
    commander: str
    services: tuple[str, ...]
    started_utc: str
    detected_by: str
    slo_impact: str
    action_items: tuple[str, ...] = field(default=())

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"severity must be one of {sorted(SEVERITIES)}")
        if not self.services:
            raise ValueError("an incident must name at least one service")


def render_runbook(profile: ServiceProfile) -> str:
    endpoints = "\n".join(f"| `{ep}` | | |" for ep in profile.endpoints)
    boards = "\n".join(f"- {d}" for d in profile.dashboards)
    return f"""# Runbook: {profile.name}

Owner: {profile.owner} | SLO: {profile.slo_target:.3%} availability (30d rolling)

## 1. Service summary
One paragraph: what {profile.name} does, who calls it, what breaks when it
breaks.

## 2. SLOs and alert entry points
| Endpoint | SLI | Alert |
|---|---|---|
{endpoints}

Dashboards:
{boards}

## 3. Triage checklist (first 10 minutes)
1. Confirm the alert is real: check the SLO dashboard, not one log line.
2. Declare severity (see severity table) and open an incident channel.
3. Capture the current trace exemplars before mitigation flushes them.

## 4. Mitigation
- Rollback: `{profile.rollback_command}`
- Feature flag: <flag name and console path>
- Traffic shift / drain: <load balancer procedure>

## 5. Escalation
- Primary on-call -> secondary (15 min ack) -> engineering manager.
"""


def render_postmortem(meta: IncidentMetadata) -> str:
    items = "\n".join(f"- [ ] {a}" for a in meta.action_items) or "- [ ] <action>"
    services = ", ".join(meta.services)
    return f"""# Postmortem: {meta.incident_id} -- {meta.title}

**Severity:** {meta.severity} ({SEVERITIES[meta.severity]})
**Incident commander:** {meta.commander}
**Services:** {services}
**Started (UTC):** {meta.started_utc}
**Detected by:** {meta.detected_by}
**SLO impact:** {meta.slo_impact}

> This document is blameless. We analyze systems, not people: any engineer
> in the same situation, with the same information, might have done the
> same thing. Naming a person as a cause voids the review.

## Summary
Two sentences a VP can read.

## Impact
Who was affected, for how long, in what units (requests failed, SLO budget
burned, revenue or contractual exposure).

## Timeline (all times UTC)
| Time | Event |
|---|---|
| | detection (alert or human?) |
| | mitigation applied |
| | full recovery |

## Root cause
The mechanism, not the culprit: what change, what assumption failed, why
existing guardrails did not catch it.

## What went well / what went poorly
Detection latency, mitigation latency, runbook accuracy, paging quality.

## Action items
{items}

## Lessons for the SLO
Did the alerts fire at the right time? Was the burn-rate table tuned
correctly, or did this incident reveal a gap (add a row, adjust a window)?
"""


def write_artifacts(out_dir: Path, profile: ServiceProfile, meta: IncidentMetadata) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"runbook_{profile.name}.md").write_text(render_runbook(profile), encoding="utf-8")
    (out_dir / f"postmortem_{meta.incident_id}.md").write_text(
        render_postmortem(meta), encoding="utf-8"
    )


def _demo() -> None:
    profile = ServiceProfile(
        name="fleet-telemetry",
        slo_target=0.999,
        owner="fleet-platform@northwind-robotics.example",
        endpoints=("POST /fleet/telemetry", "GET /fleet/status", "GET /health"),
        dashboards=("SLO / fleet-telemetry (Grafana uid=nr-fleet-slo)",
                    "RED / per-endpoint (Grafana uid=nr-fleet-red)"),
        rollback_command="kubectl rollout undo deploy/fleet-telemetry",
    )
    meta = IncidentMetadata(
        incident_id="NR-2026-0142",
        title="Retry storm after inventory latency regression",
        severity="SEV2",
        commander="a.reyes",
        services=("fleet-gateway", "orders", "inventory"),
        started_utc="2026-08-19T14:03Z",
        detected_by="fast-burn SLO alert (14.4x, 1h/5m)",
        slo_impact="41% of monthly availability budget in 52 minutes",
        action_items=(
            "Cap gateway retries at 2 with jitter (owner: fleet-platform)",
            "Add fan-out panel (requests per client request) to the SLO board",
        ),
    )
    write_artifacts(Path("incident_docs"), profile, meta)
    print(render_postmortem(meta).splitlines()[0])
    print("wrote incident_docs/runbook_fleet-telemetry.md and",
          "incident_docs/postmortem_NR-2026-0142.md")


# ---------------------------------------------------------------------------
# Embedded test suite: pytest incident_templates.py -q
# ---------------------------------------------------------------------------
def _profile() -> ServiceProfile:
    return ServiceProfile(
        name="orders", slo_target=0.9995, owner="orders@northwind-robotics.example",
        endpoints=("POST /orders",), dashboards=("SLO / orders",),
        rollback_command="kubectl rollout undo deploy/orders",
    )


def _meta() -> IncidentMetadata:
    return IncidentMetadata(
        incident_id="NR-2026-0001", title="Test incident", severity="SEV3",
        commander="oncall", services=("orders",), started_utc="2026-01-01T00:00Z",
        detected_by="test", slo_impact="none",
    )


def test_runbook_has_all_mandatory_sections() -> None:
    text = render_runbook(_profile())
    for section in ("Service summary", "SLOs and alert entry points",
                    "Triage checklist", "Mitigation", "Escalation"):
        assert f"## " in text and section in text, f"missing section: {section}"
    assert "kubectl rollout undo deploy/orders" in text
    assert "99.950%" in text  # SLO rendered as a percentage


def test_postmortem_is_blameless_and_complete() -> None:
    text = render_postmortem(_meta())
    for section in ("Summary", "Impact", "Timeline", "Root cause",
                    "Action items", "Lessons for the SLO"):
        assert section in text, f"missing section: {section}"
    assert "blameless" in text.lower()
    assert "SEV3" in text


def test_invalid_severity_rejected() -> None:
    import pytest

    with pytest.raises(ValueError):
        IncidentMetadata(
            incident_id="X", title="t", severity="SEV9", commander="c",
            services=("s",), started_utc="2026-01-01T00:00Z",
            detected_by="test", slo_impact="none",
        )
    with pytest.raises(ValueError):
        IncidentMetadata(
            incident_id="X", title="t", severity="SEV1", commander="c",
            services=(), started_utc="2026-01-01T00:00Z",
            detected_by="test", slo_impact="none",
        )


def test_write_artifacts(tmp_path: Path) -> None:
    write_artifacts(tmp_path, _profile(), _meta())
    assert (tmp_path / "runbook_orders.md").exists()
    assert (tmp_path / "postmortem_NR-2026-0001.md").exists()


if __name__ == "__main__":
    _demo()
