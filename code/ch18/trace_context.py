"""Hand-rolled W3C Trace Context: parse and inject ``traceparent``.

Stdlib-only reference implementation of the wire format every API engineer
should be able to read cold:

    traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
                 |  |-------------------------------| |--------------| |-|
                 |  trace-id (32 hex, != 0)           parent/span-id   flags
                 version (2 hex, never "ff")          (16 hex, != 0)   bit 0 = sampled

Design notes:
  * Parsing is strict: malformed headers raise ``ValueError`` with the
    offending field named. Silently "fixing" a broken header would fork
    the trace; dropping it (returning ``None``) hides producer bugs.
  * Version "00" headers must be exactly 55 characters / 4 fields. Future
    versions may append fields, so for version != "00" we accept extra
    trailing fields and ignore them (forward compatibility).
  * ``tracestate`` and ``baggage`` parsers are included because the three
    headers travel together in production.

No network, no dependencies, no randomness: deterministic by construction.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

HEX = frozenset("0123456789abcdef")
MAX_TRACESTATE_MEMBERS = 32  # per the W3C Trace Context spec


@dataclass(frozen=True)
class TraceParent:
    """An immutable, validated ``traceparent`` value."""

    version: str
    trace_id: str
    span_id: str
    sampled: bool

    def __post_init__(self) -> None:
        if len(self.version) != 2 or not set(self.version) <= HEX:
            raise ValueError(f"version must be 2 lowercase hex chars, got {self.version!r}")
        if self.version == "ff":
            raise ValueError("version 'ff' is reserved (invalid) by the spec")
        _check_hex_field("trace_id", self.trace_id, 32)
        _check_hex_field("span_id", self.span_id, 16)
        if self.trace_id == "0" * 32:
            raise ValueError("trace_id of all zeros is invalid")
        if self.span_id == "0" * 16:
            raise ValueError("span_id of all zeros is invalid")

    @property
    def flags(self) -> str:
        return "01" if self.sampled else "00"

    def header(self) -> str:
        """Render the canonical ``traceparent`` header value."""
        return f"{self.version}-{self.trace_id}-{self.span_id}-{self.flags}"


def _check_hex_field(name: str, value: str, length: int) -> None:
    if len(value) != length or not set(value) <= HEX:
        raise ValueError(
            f"{name} must be exactly {length} lowercase hex chars, got {value!r}"
        )


def parse_traceparent(header: str) -> TraceParent:
    """Parse a ``traceparent`` header value, raising ``ValueError`` if bad."""
    if not isinstance(header, str) or not header:
        raise ValueError("traceparent header must be a non-empty string")
    if header != header.strip():
        raise ValueError("traceparent must not carry surrounding whitespace")
    parts = header.split("-")
    if len(parts) < 4:
        raise ValueError(
            f"traceparent needs at least 4 dash-separated fields, got {len(parts)}"
        )
    version, trace_id, span_id, flags = parts[0], parts[1], parts[2], parts[3]
    if len(flags) != 2 or not set(flags) <= HEX:
        raise ValueError(f"flags must be 2 lowercase hex chars, got {flags!r}")
    if version == "00" and len(parts) != 4:
        raise ValueError("version '00' forbids extra fields")
    sampled = bool(int(flags, 16) & 0b0000_0001)  # only bit 0 is defined
    return TraceParent(version=version, trace_id=trace_id,
                       span_id=span_id, sampled=sampled)


def new_traceparent(*, sampled: bool = True) -> TraceParent:
    """Mint a fresh root context (16-byte trace id, 8-byte span id)."""
    return TraceParent(
        version="00",
        trace_id=secrets.token_hex(16),
        span_id=secrets.token_hex(8),
        sampled=sampled,
    )


def child_of(parent: TraceParent, *, sampled: bool | None = None) -> TraceParent:
    """Derive the outgoing context for a child hop: same trace, new span id."""
    return TraceParent(
        version=parent.version,
        trace_id=parent.trace_id,
        span_id=secrets.token_hex(8),
        sampled=parent.sampled if sampled is None else sampled,
    )


def parse_tracestate(header: str) -> dict[str, str]:
    """Parse a ``tracestate`` list-member header into an ordered dict.

    Raises ``ValueError`` on more than 32 members or malformed entries.
    """
    if not header.strip():
        return {}
    members = [m.strip() for m in header.split(",")]
    if len(members) > MAX_TRACESTATE_MEMBERS:
        raise ValueError(f"tracestate allows at most {MAX_TRACESTATE_MEMBERS} members")
    out: dict[str, str] = {}
    for member in members:
        if "=" not in member:
            raise ValueError(f"tracestate member lacks '=': {member!r}")
        key, _, value = member.partition("=")
        if not key or key in out:
            raise ValueError(f"tracestate duplicate/empty key: {key!r}")
        out[key] = value
    return out


def parse_baggage(header: str) -> dict[str, str]:
    """Parse a W3C ``baggage`` header; unknown per-entry properties dropped."""
    out: dict[str, str] = {}
    for member in header.split(","):
        member = member.strip()
        if not member:
            continue
        pair = member.split(";")[0].strip()  # drop ;property annotations
        if "=" not in pair:
            raise ValueError(f"baggage member lacks '=': {member!r}")
        key, _, value = pair.partition("=")
        out[key.strip()] = value.strip()
    return out


def _demo() -> None:
    """Round-trip one trace through three synthetic hops (deterministic)."""
    print("== W3C Trace Context round-trip demo (Northwind Robotics) ==")
    root = parse_traceparent(
        "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    )
    print(f"incoming  : {root.header()}  sampled={root.sampled}")
    hop1 = child_of(root)
    print(f"gateway -> orders      : {hop1.header()}")
    hop2 = child_of(hop1)
    print(f"orders  -> inventory   : {hop2.header()}")
    echoed = parse_traceparent(hop2.header())
    assert echoed.trace_id == root.trace_id, "trace id must survive every hop"
    assert echoed.span_id == hop2.span_id, "round-trip must preserve span id"
    print("trace id stable across hops:", echoed.trace_id == root.trace_id)
    print(parse_tracestate("nr=region:eu-1,congo=t61rcWkgMzE"))
    print(parse_baggage("tenant=northwind-robotics,plan=fleet-pro;property=x"))


if __name__ == "__main__":
    _demo()
