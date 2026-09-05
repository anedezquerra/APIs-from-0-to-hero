"""Instrumented FastAPI service: traces, metrics, and correlated logs.

Northwind Robotics fleet-telemetry platform, offline edition. The OTLP
exporter you would point at a real collector is replaced by
``JsonlSpanExporter`` (spans to a local JSON-lines file) and an
``InMemoryMetricReader`` (metrics read back from the SDK), so the whole
demo runs with no collector, no network, and no credentials.

Telemetry wiring:
  * one ``TracerProvider`` with a seeded ID generator (deterministic tests)
  * one ``MeterProvider`` with explicit-bucket histogram views (RED metrics)
  * a ``logging.Formatter`` that stamps every record with trace_id/span_id
    of the *active* span, so a log line and a trace never drift apart

Propagation demo: a synthetic incoming ``traceparent`` header is extracted
at the gateway, and each internal hop injects the current context into a
fresh carrier dict --- the exact bytes that would ride the wire in
production. The exported span tree proves all three hops share one
trace_id and nest parent -> child correctly.

Run:  python instrumented_app.py
Serve (optional, needs uvicorn):  uvicorn instrumented_app:app
"""

from __future__ import annotations

import json
import logging
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.metrics.view import ExplicitBucketHistogramAggregation, View
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from opentelemetry.sdk.trace.id_generator import IdGenerator
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from opentelemetry.trace.propagation.tracecontext import (
    TraceContextTextMapPropagator,
)
from opentelemetry.trace import SpanKind

LATENCY_BUCKETS_MS = [5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 2500.0]
PROPAGATOR = TraceContextTextMapPropagator()


# --------------------------------------------------------------------------
# Telemetry plumbing
# --------------------------------------------------------------------------
class SeededIdGenerator(IdGenerator):
    """Deterministic trace/span IDs so tests assert exact span trees."""

    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)

    def generate_trace_id(self) -> int:
        return max(1, self._rng.getrandbits(128))  # all-zero id is invalid

    def generate_span_id(self) -> int:
        return max(1, self._rng.getrandbits(64))


class JsonlSpanExporter(SpanExporter):
    """Offline OTLP replacement: append finished spans to a JSONL file."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.write_text("", encoding="utf-8")

    def export(self, spans: Sequence[trace.Span]) -> SpanExportResult:
        with self._path.open("a", encoding="utf-8") as fh:
            for span in spans:
                fh.write(json.dumps(_span_to_dict(span)) + "\n")
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:  # nothing buffered; file handles are scoped
        return None


def _span_to_dict(span: trace.Span) -> dict[str, object]:
    ctx = span.get_span_context()
    parent = span.parent
    return {
        "name": span.name,
        "kind": span.kind.name if span.kind else "INTERNAL",
        "trace_id": f"{ctx.trace_id:032x}",
        "span_id": f"{ctx.span_id:016x}",
        "parent_span_id": f"{parent.span_id:016x}" if parent else None,
        "duration_ms": round((span.end_time - span.start_time) / 1e6, 3),
        "attributes": {k: v for k, v in (span.attributes or {}).items()},
        "status": span.status.status_code.name,
    }


class TraceContextFilter(logging.Filter):
    """Stamps trace_id/span_id of the active span onto every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        ctx = trace.get_current_span().get_span_context()
        record.trace_id = f"{ctx.trace_id:032x}" if ctx.trace_id else "-"
        record.span_id = f"{ctx.span_id:016x}" if ctx.span_id else "-"
        return True


class JsonFormatter(logging.Formatter):
    """One JSON object per line; never log headers, tokens, or payloads."""

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "trace_id": getattr(record, "trace_id", "-"),
            "span_id": getattr(record, "span_id", "-"),
        })


@dataclass
class Telemetry:
    """Everything an instrumented service needs, wired offline."""

    provider: TracerProvider
    tracer: trace.Tracer
    exporter_path: Path
    meter_reader: InMemoryMetricReader
    request_counter: object
    request_duration: object
    logger: logging.Logger
    log_lines: list[str] = field(default_factory=list)


def build_telemetry(seed: int = 18, spans_path: Path = Path("spans.jsonl")) -> Telemetry:
    resource = Resource.create({"service.name": "nr-fleet-telemetry"})
    provider = TracerProvider(
        sampler=ALWAYS_ON,
        id_generator=SeededIdGenerator(seed),
        resource=resource,
    )
    provider.add_span_processor(SimpleSpanProcessor(JsonlSpanExporter(spans_path)))

    reader = InMemoryMetricReader()
    view = View(
        instrument_name="http.server.request.duration",
        aggregation=ExplicitBucketHistogramAggregation(boundaries=LATENCY_BUCKETS_MS),
    )
    meter_provider = MeterProvider(
        metric_readers=[reader], views=[view], resource=resource
    )
    meter = meter_provider.get_meter("nr.fleet")

    logger = logging.getLogger("nr.fleet")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    telemetry = Telemetry(
        provider=provider,
        tracer=provider.get_tracer("nr.fleet"),
        exporter_path=spans_path,
        meter_reader=reader,
        request_counter=meter.create_counter(
            "http.server.request.count",
            description="Total HTTP requests (RED: rate, errors)",
        ),
        request_duration=meter.create_histogram(
            "http.server.request.duration",
            unit="ms",
            description="Request latency histogram (RED: duration)",
        ),
        logger=logger,
    )
    return telemetry


# --------------------------------------------------------------------------
# Service layer: a three-hop internal call chain
# --------------------------------------------------------------------------
def inventory_reserve(telemetry: Telemetry, carrier: dict[str, str]) -> dict[str, object]:
    """Hop 3 (deepest): check stock. Extracts context from its carrier."""
    ctx = PROPAGATOR.extract(carrier=carrier)
    with telemetry.tracer.start_as_current_span(
        "inventory.reserve", context=ctx, kind=SpanKind.SERVER
    ) as span:
        span.set_attribute("peer.service", "inventory")
        span.set_attribute("warehouse", "eu-1")
        time.sleep(0.004)  # deterministic-ish work stand-in; tests don't time it
        telemetry.logger.info("stock reserved sku=NR-GRIP-4 qty=2")
        return {"sku": "NR-GRIP-4", "reserved": 2}


def orders_create(telemetry: Telemetry, carrier: dict[str, str]) -> dict[str, object]:
    """Hop 2: create the resupply order; injects context for hop 3."""
    ctx = PROPAGATOR.extract(carrier=carrier)
    with telemetry.tracer.start_as_current_span(
        "orders.create", context=ctx, kind=SpanKind.SERVER
    ) as span:
        span.set_attribute("peer.service", "orders")
        span.set_attribute("order.kind", "resupply")
        outbound: dict[str, str] = {}
        PROPAGATOR.inject(outbound)  # traceparent bytes for the next hop
        reservation = inventory_reserve(telemetry, outbound)
        telemetry.logger.info("order created id=NR-2026-0917")
        return {"order_id": "NR-2026-0917", "reservation": reservation}


def gateway_handle(telemetry: Telemetry, headers: Mapping[str, str]) -> dict[str, object]:
    """Hop 1 (edge): extract the client-supplied traceparent, record RED."""
    started = time.perf_counter()
    status = 200
    ctx = PROPAGATOR.extract(carrier=dict(headers))
    with telemetry.tracer.start_as_current_span(
        "gateway POST /fleet/telemetry", context=ctx, kind=SpanKind.SERVER
    ) as span:
        span.set_attribute("http.request.method", "POST")
        span.set_attribute("url.path", "/fleet/telemetry")
        span.set_attribute("http.response.status_code", status)
        outbound: dict[str, str] = {}
        PROPAGATOR.inject(outbound)
        try:
            result = orders_create(telemetry, outbound)
        except Exception:
            status = 500
            span.set_attribute("http.response.status_code", status)
            raise
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            attrs = {"route": "/fleet/telemetry", "status": status}
            telemetry.request_counter.add(1, attrs)
            telemetry.request_duration.record(elapsed_ms, attrs)
        telemetry.logger.info("request complete status=200")
        return result


# --------------------------------------------------------------------------
# FastAPI wiring (thin adapters over the instrumented service layer)
# --------------------------------------------------------------------------
telemetry = build_telemetry()
app = FastAPI(title="Northwind Robotics Fleet Telemetry")
FastAPIInstrumentor.instrument_app(
    app, tracer_provider=telemetry.provider, excluded_urls="/health"
)


@app.middleware("http")
async def correlate_logs(request: Request, call_next):  # noqa: ANN001
    # The instrumentor's server span is active here, so logs pick up its ids.
    response: JSONResponse = await call_next(request)
    telemetry.logger.info(
        "http request method=%s path=%s status=%s",
        request.method, request.url.path, response.status_code,
    )
    return response


@app.post("/fleet/telemetry")
async def ingest(request: Request) -> dict[str, object]:
    return gateway_handle(telemetry, dict(request.headers))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# --------------------------------------------------------------------------
# Offline demo: drive the service layer with a synthetic traceparent
# --------------------------------------------------------------------------
def _demo() -> None:
    telemetry = build_telemetry(seed=18, spans_path=Path("spans.jsonl"))

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(TraceContextFilter())
    telemetry.logger.addHandler(handler)

    incoming = {
        "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        "tracestate": "nr=region:eu-1",
    }
    print("== three-hop trace, one synthetic incoming traceparent ==")
    result = gateway_handle(telemetry, incoming)
    telemetry.provider.force_flush()

    lines = telemetry.exporter_path.read_text(encoding="utf-8").splitlines()
    spans = [json.loads(line) for line in lines if line.strip()]
    print(f"exported {len(spans)} spans:")
    for s in sorted(spans, key=lambda s: s["parent_span_id"] is not None):
        print(
            f"  {s['name']:<32} kind={s['kind']:<8} "
            f"trace={s['trace_id'][:12]}... span={s['span_id']} "
            f"parent={s['parent_span_id']}"
        )
    trace_ids = {s["trace_id"] for s in spans}
    by_name = {s["name"]: s for s in spans}
    assert len(trace_ids) == 1, "all hops must share one trace_id"
    assert trace_ids == {"4bf92f3577b34da6a3ce929d0e0e4736"}, (
        "incoming trace_id must survive every hop"
    )
    assert by_name["orders.create"]["parent_span_id"] == by_name[
        "gateway POST /fleet/telemetry"]["span_id"]
    assert by_name["inventory.reserve"]["parent_span_id"] == by_name[
        "orders.create"]["span_id"]
    print("propagation verified: one trace_id, correct parent chain")

    data = telemetry.meter_reader.get_metrics_data()
    for rm in data.resource_metrics:
        for sm in rm.scope_metrics:
            for m in sm.metrics:
                pts = list(m.data.data_points)
                print(f"metric {m.name}: points={len(pts)}")
    print(f"result: {json.dumps(result)}")


if __name__ == "__main__":
    _demo()
