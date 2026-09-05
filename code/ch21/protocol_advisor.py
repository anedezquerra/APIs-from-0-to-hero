"""Protocol-selection advisor for the Master Decision Card.

Encodes the Chapter 21 decision framework as a scored questionnaire:
weighted criteria, deterministic arithmetic, and a full rationale trace
so the recommendation can be audited and taught from.

Offline, deterministic, standard library only. Python 3.11+.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Profile(str, Enum):
    """API interaction profiles compared by the advisor."""

    REST = "REST"
    GRAPHQL = "GraphQL"
    GRPC = "gRPC"
    EVENTS = "Event-driven (webhooks/broker)"
    STREAM = "WebSockets / SSE"


class Consumer(str, Enum):
    PUBLIC = "public-third-party"
    MOBILE = "mobile-spa"
    INTERNAL = "internal-service"
    MACHINE = "machine-telemetry"


class Payload(str, Enum):
    FIXED = "fixed-resources"
    GRAPH = "nested-graph"
    HIGH_VOLUME = "high-volume-streams"


class Latency(str, Enum):
    RELAXED = "relaxed"      # p99 >= 200 ms is fine
    TIGHT = "tight"          # interactive, p99 < 200 ms
    EXTREME = "extreme"      # p99 < 50 ms service-to-service


class Delivery(str, Enum):
    SYNC = "sync-request-response"
    PUSH = "server-push-realtime"
    ASYNC = "async-fire-and-forget"


class Team(str, Enum):
    EXPLORATORY = "exploratory"
    DISCIPLINED = "disciplined"


@dataclass(frozen=True)
class Requirements:
    """Answers to the six-question selection questionnaire."""

    consumer: Consumer
    payload: Payload
    latency: Latency
    delivery: Delivery
    http_caching: bool
    team: Team


@dataclass(frozen=True)
class Signal:
    """One weighted contribution to a profile's score."""

    profile: Profile
    points: int
    criterion: str
    rationale: str


@dataclass(frozen=True)
class Recommendation:
    """Advisor output: ranked scores plus an auditable trace."""

    winner: Profile
    scores: dict[Profile, int]
    signals: tuple[Signal, ...] = field(default_factory=tuple)

    def rationale(self, profile: Profile | None = None) -> list[str]:
        """Return the trace lines for one profile (default: the winner)."""
        target = profile or self.winner
        return [
            f"[{s.points:+d}] {s.criterion}: {s.rationale}"
            for s in self.signals
            if s.profile == target
        ]


def _score(req: Requirements) -> tuple[Signal, ...]:
    """Apply every rule of the Master Decision Card to the answers."""
    signals: list[Signal] = []

    def add(profile: Profile, points: int, criterion: str, rationale: str) -> None:
        signals.append(Signal(profile, points, criterion, rationale))

    # --- Criterion 1: consumer type -------------------------------------
    if req.consumer is Consumer.PUBLIC:
        add(Profile.REST, 3, "consumer",
            "public third parties expect plain HTTPS + JSON they can curl")
        add(Profile.EVENTS, 2, "consumer",
            "webhooks are the standard public async contract")
        add(Profile.GRAPHQL, 1, "consumer",
            "powerful for public developers but raises the support burden")
        add(Profile.GRPC, -3, "consumer",
            "browser clients cannot speak raw HTTP/2 gRPC without a proxy")
        add(Profile.STREAM, 1, "consumer",
            "SSE/WebSocket endpoints are feasible but operationally niche")
    elif req.consumer is Consumer.MOBILE:
        add(Profile.GRAPHQL, 3, "consumer",
            "clients pick exactly the fields they render; no over-fetching")
        add(Profile.REST, 2, "consumer",
            "aggregating BFF-style REST resources also solve over-fetching")
        add(Profile.STREAM, 1, "consumer",
            "push channels pair well with mobile UX")
        add(Profile.GRPC, -2, "consumer",
            "gRPC-Web adds a proxy hop that mobile teams rarely want")
    elif req.consumer is Consumer.INTERNAL:
        add(Profile.GRPC, 3, "consumer",
            "strongly typed, streaming, low-overhead service-to-service RPC")
        add(Profile.REST, 1, "consumer",
            "REST remains the default when tooling maturity is low")
        add(Profile.EVENTS, 1, "consumer",
            "async integration decouples internal services")
        add(Profile.GRAPHQL, 1, "consumer",
            "federated graphs can front many internal services")
    else:  # MACHINE telemetry
        add(Profile.EVENTS, 3, "consumer",
            "telemetry is naturally asynchronous and bursty")
        add(Profile.GRPC, 2, "consumer",
            "bidirectional streaming fits high-rate device channels")
        add(Profile.STREAM, 1, "consumer",
            "persistent sockets work where HTTP/2 is unavailable")
        add(Profile.REST, -1, "consumer",
            "per-reading REST calls waste headers and connections")

    # --- Criterion 2: payload shape -------------------------------------
    if req.payload is Payload.GRAPH:
        add(Profile.GRAPHQL, 3, "payload",
            "nested graph selection sets are GraphQL's home turf")
        add(Profile.REST, -1, "payload",
            "deep graphs force N+1 endpoint hops in REST")
    elif req.payload is Payload.HIGH_VOLUME:
        add(Profile.GRPC, 2, "payload",
            "compact binary frames and HTTP/2 streams suit high volume")
        add(Profile.EVENTS, 2, "payload",
            "brokered batches absorb volume spikes")
        add(Profile.REST, -1, "payload",
            "textual JSON per request is the most expensive option")
    else:
        add(Profile.REST, 2, "payload",
            "fixed resource shapes map one-to-one onto REST resources")

    # --- Criterion 3: latency budget ------------------------------------
    if req.latency is Latency.EXTREME:
        add(Profile.GRPC, 3, "latency",
            "HTTP/2 multiplexing plus Protobuf minimize per-call overhead")
        add(Profile.GRAPHQL, -1, "latency",
            "query planning and JSON add milliseconds per request")
        add(Profile.REST, 0, "latency",
            "acceptable with keep-alive and HTTP/2, but not minimal")
    elif req.latency is Latency.TIGHT:
        add(Profile.GRPC, 1, "latency", "comfortable within tight budgets")
        add(Profile.REST, 1, "latency", "comfortable within tight budgets")
    else:
        add(Profile.EVENTS, 2, "latency",
            "async delivery tolerates relaxed latency by design")

    # --- Criterion 4: delivery model (hard structural signals) ----------
    if req.delivery is Delivery.PUSH:
        add(Profile.STREAM, 4, "delivery",
            "server push requires SSE or WebSockets; unary APIs cannot push")
        add(Profile.GRPC, 1, "delivery",
            "server-streaming RPC works for non-browser clients")
        add(Profile.REST, -3, "delivery",
            "unary REST has no server-push channel")
        add(Profile.GRAPHQL, -2, "delivery",
            "GraphQL subscriptions need a socket transport anyway")
    elif req.delivery is Delivery.ASYNC:
        add(Profile.EVENTS, 4, "delivery",
            "fire-and-forget delivery is the defining event-driven case")
    else:
        add(Profile.REST, 1, "delivery",
            "synchronous request-response is REST's native shape")
        add(Profile.GRPC, 1, "delivery",
            "unary RPC is also synchronous request-response")

    # --- Criterion 5: HTTP caching --------------------------------------
    if req.http_caching:
        add(Profile.REST, 3, "caching",
            "only REST leverages shared/CDN caching of GET responses")
        add(Profile.GRAPHQL, -2, "caching",
            "POST-based queries bypass standard HTTP caches")
        add(Profile.GRPC, -2, "caching",
            "gRPC calls are not addressable cacheable resources")
    else:
        add(Profile.GRAPHQL, 1, "caching",
            "no penalty when edge caching is not required")

    # --- Criterion 6: team maturity -------------------------------------
    if req.team is Team.EXPLORATORY:
        add(Profile.REST, 2, "team",
            "REST has the shallowest learning curve and richest tooling")
        add(Profile.GRPC, -1, "team",
            "Protobuf toolchains and reflection quirks slow new teams")
        add(Profile.GRAPHQL, -1, "team",
            "schema governance and N+1 discipline require experience")
    else:
        add(Profile.GRAPHQL, 1, "team",
            "disciplined teams can exploit schema-first workflows")
        add(Profile.GRPC, 1, "team",
            "disciplined teams can run contract-first RPC safely")

    return tuple(signals)


def recommend(req: Requirements) -> Recommendation:
    """Score all profiles and return the winner with a rationale trace.

    Ties break deterministically by profile enum order, so the same
    answers always produce the same recommendation.
    """
    signals = _score(req)
    scores = {profile: 0 for profile in Profile}
    for signal in signals:
        scores[signal.profile] += signal.points
    winner = max(Profile, key=lambda p: (scores[p], -list(Profile).index(p)))
    return Recommendation(winner=winner, scores=scores, signals=signals)


# --- Canonical scenarios from the chapter's worked examples ---------------

PUBLIC_SAAS = Requirements(
    consumer=Consumer.PUBLIC,
    payload=Payload.FIXED,
    latency=Latency.RELAXED,
    delivery=Delivery.SYNC,
    http_caching=True,
    team=Team.DISCIPLINED,
)

INTERNAL_MESH = Requirements(
    consumer=Consumer.INTERNAL,
    payload=Payload.FIXED,
    latency=Latency.EXTREME,
    delivery=Delivery.SYNC,
    http_caching=False,
    team=Team.DISCIPLINED,
)

MOBILE_BACKEND = Requirements(
    consumer=Consumer.MOBILE,
    payload=Payload.GRAPH,
    latency=Latency.TIGHT,
    delivery=Delivery.SYNC,
    http_caching=False,
    team=Team.DISCIPLINED,
)

IOT_TELEMETRY = Requirements(
    consumer=Consumer.MACHINE,
    payload=Payload.HIGH_VOLUME,
    latency=Latency.RELAXED,
    delivery=Delivery.ASYNC,
    http_caching=False,
    team=Team.DISCIPLINED,
)

PARTNER_NOTIFICATIONS = Requirements(
    consumer=Consumer.PUBLIC,
    payload=Payload.FIXED,
    latency=Latency.RELAXED,
    delivery=Delivery.ASYNC,
    http_caching=False,
    team=Team.EXPLORATORY,
)


if __name__ == "__main__":
    scenarios = {
        "Public SaaS API": PUBLIC_SAAS,
        "Internal microservice mesh": INTERNAL_MESH,
        "Mobile app backend": MOBILE_BACKEND,
        "IoT telemetry": IOT_TELEMETRY,
        "Partner notifications": PARTNER_NOTIFICATIONS,
    }
    for name, reqs in scenarios.items():
        rec = recommend(reqs)
        print(f"{name}: {rec.winner.value}")
        for line in rec.rationale():
            print(f"    {line}")
