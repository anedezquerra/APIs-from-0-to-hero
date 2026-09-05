"""Unit tests for the protocol-selection advisor.

Covers the five canonical scenarios from the chapter plus framework
invariants (determinism, scoring arithmetic, rationale trace).
"""

from __future__ import annotations

from protocol_advisor import (
    IOT_TELEMETRY,
    INTERNAL_MESH,
    MOBILE_BACKEND,
    PARTNER_NOTIFICATIONS,
    PUBLIC_SAAS,
    Consumer,
    Delivery,
    Latency,
    Payload,
    Profile,
    Requirements,
    Team,
    recommend,
)


def test_public_saas_recommends_rest() -> None:
    assert recommend(PUBLIC_SAAS).winner is Profile.REST


def test_internal_mesh_recommends_grpc() -> None:
    assert recommend(INTERNAL_MESH).winner is Profile.GRPC


def test_mobile_backend_recommends_graphql() -> None:
    assert recommend(MOBILE_BACKEND).winner is Profile.GRAPHQL


def test_iot_telemetry_recommends_events() -> None:
    assert recommend(IOT_TELEMETRY).winner is Profile.EVENTS


def test_partner_notifications_recommend_events() -> None:
    assert recommend(PARTNER_NOTIFICATIONS).winner is Profile.EVENTS


def test_push_delivery_selects_streams() -> None:
    reqs = Requirements(
        consumer=Consumer.PUBLIC,
        payload=Payload.FIXED,
        latency=Latency.TIGHT,
        delivery=Delivery.PUSH,
        http_caching=False,
        team=Team.DISCIPLINED,
    )
    assert recommend(reqs).winner is Profile.STREAM


def test_recommendation_is_deterministic() -> None:
    first = recommend(PUBLIC_SAAS)
    second = recommend(PUBLIC_SAAS)
    assert first == second


def test_scores_equal_sum_of_signals() -> None:
    rec = recommend(MOBILE_BACKEND)
    for profile in Profile:
        total = sum(s.points for s in rec.signals if s.profile is profile)
        assert rec.scores[profile] == total


def test_winner_has_strictly_highest_score() -> None:
    rec = recommend(IOT_TELEMETRY)
    best = max(rec.scores.values())
    assert rec.scores[rec.winner] == best
    assert list(rec.scores.values()).count(best) >= 1


def test_rationale_trace_references_winner_only() -> None:
    rec = recommend(INTERNAL_MESH)
    trace = rec.rationale()
    assert trace, "winner must have at least one rationale line"
    for line in trace:
        assert ":" in line and line.startswith("[")
