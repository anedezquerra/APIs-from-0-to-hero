"""Executable proof sheet for trace_context.py (run: pytest -q)."""

from __future__ import annotations

import pytest

from trace_context import (
    TraceParent,
    child_of,
    new_traceparent,
    parse_baggage,
    parse_traceparent,
    parse_tracestate,
)

VALID = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"


def test_round_trip_preserves_every_field() -> None:
    tp = parse_traceparent(VALID)
    assert tp.header() == VALID
    assert tp.version == "00"
    assert tp.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert tp.span_id == "00f067aa0ba902b7"
    assert tp.sampled is True


def test_not_sampled_flag() -> None:
    tp = parse_traceparent(VALID[:-2] + "00")
    assert tp.sampled is False
    assert tp.header().endswith("-00")


def test_flags_bitmask_ignores_undefined_bits() -> None:
    # only bit 0 (0x01) is the sampled flag; other bits must not leak in
    tp = parse_traceparent(VALID[:-2] + "03")
    assert tp.sampled is True
    assert tp.flags == "01"  # canonical rendering keeps only defined bits


def test_child_keeps_trace_id_and_gets_fresh_span_id() -> None:
    root = parse_traceparent(VALID)
    child = child_of(root)
    assert child.trace_id == root.trace_id
    assert child.span_id != root.span_id
    assert len(child.span_id) == 16
    assert child.sampled == root.sampled


def test_new_contexts_are_well_formed() -> None:
    tp = new_traceparent()
    again = parse_traceparent(tp.header())
    assert again == tp


@pytest.mark.parametrize(
    "bad",
    [
        "",                                   # empty
        VALID.upper(),                        # uppercase hex forbidden
        "ff-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",  # ff version
        "00-00000000000000000000000000000000-00f067aa0ba902b7-01",  # zero trace id
        "00-4bf92f3577b34da6a3ce929d0e0e4736-0000000000000000-01",  # zero span id
        "00-4bf92f3577b34da6a3ce929d0e0e473-00f067aa0ba902b7-01",   # short trace id
        "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7",     # missing flags
        "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-0g",  # bad hex flag
        "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01-extra",  # v00 extra field
        " 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",  # whitespace
    ],
)
def test_rejects_malformed_headers(bad: str) -> None:
    with pytest.raises(ValueError):
        parse_traceparent(bad)


def test_future_version_may_append_fields() -> None:
    # forward compatibility: version 01 with a trailing field parses fine
    tp = parse_traceparent("01-" + VALID[3:] + "-congo")
    assert tp.version == "01"


def test_tracestate_round_trip_and_limits() -> None:
    state = parse_tracestate("nr=region:eu-1,congo=t61rcWkgMzE")
    assert state == {"nr": "region:eu-1", "congo": "t61rcWkgMzE"}
    with pytest.raises(ValueError):
        parse_tracestate(",".join(f"k{i}=v" for i in range(33)))
    with pytest.raises(ValueError):
        parse_tracestate("nr=one,nr=two")  # duplicate key


def test_baggage_drops_properties() -> None:
    bag = parse_baggage("tenant=northwind-robotics;ttl=30,plan=fleet-pro")
    assert bag == {"tenant": "northwind-robotics", "plan": "fleet-pro"}
    with pytest.raises(ValueError):
        parse_baggage("no-equals-sign")


def test_immutability() -> None:
    tp = parse_traceparent(VALID)
    with pytest.raises(AttributeError):
        tp.trace_id = "0" * 32  # type: ignore[misc]
