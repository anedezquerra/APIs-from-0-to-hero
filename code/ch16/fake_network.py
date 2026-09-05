"""Simulated network for offline SSRF/API10 teaching.

In production, ``httpx`` sockets reach the real internet. In this workbook
every outbound request is routed through a deterministic in-process host
table so the exploit suite runs with zero network access. The table models
the hosts that matter for the security story: an internal-only inventory
service, the cloud instance-metadata endpoint, and an allowed partner API.
"""

from __future__ import annotations

import httpx

# Hosts that exist inside the simulated world. RFC 1918 / link-local /
# loopback addresses stand in for Northwind Robotics' private network.
HOST_TABLE: dict[str, tuple[int, dict[str, str], str]] = {
    "inventory.internal.nwr": (
        200,
        {"content-type": "application/json"},
        '{"service": "inventory", "db_dsn": "postgres://svc:FAKE_PASS_invalid@db.internal:5432/inv"}',
    ),
    "169.254.169.254": (
        200,
        {"content-type": "application/json"},
        '{"iam": {"role": "nwr-fleet-worker", "AccessKeyId": "AKIAFAKE_INVALID",'
        ' "SecretAccessKey": "sk_test_DEMO_9f8e7d6c5b4a3210_invalid"}}',
    ),
    "telemetry.partner-nwr.example": (
        200,
        {"content-type": "application/json"},
        '{"firmware": "4.2.1", "channels": ["stable"]}',
    ),
    "untrusted.maps.example": (
        200,
        {"content-type": "application/json"},
        '{"label": "Dock 7", "telemetry_channel": "beta", "maintenance_mode": true}',
    ),
}

# One simulated redirect: the "safe-looking" shortener bounces to metadata.
REDIRECTS: dict[str, str] = {
    "short.partner-nwr.example": "http://169.254.169.254/latest/meta-data",
}


def simulated_dns(host: str) -> list[str]:
    """Deterministic stand-in for DNS resolution."""
    table = {
        "inventory.internal.nwr": ["10.20.0.14"],
        "169.254.169.254": ["169.254.169.254"],
        "telemetry.partner-nwr.example": ["203.0.113.10"],
        "untrusted.maps.example": ["198.51.100.77"],
        "short.partner-nwr.example": ["203.0.113.99"],
    }
    return table.get(host, ["192.0.2.1"])  # TEST-NET-1 for anything unknown


def mock_transport(request: httpx.Request) -> httpx.Response:
    """httpx transport handler implementing the simulated network."""
    host = request.url.host or ""
    if host in REDIRECTS:
        return httpx.Response(302, headers={"location": REDIRECTS[host]})
    if host in HOST_TABLE:
        status, headers, body = HOST_TABLE[host]
        return httpx.Response(status, headers=headers, text=body)
    return httpx.Response(404, text="host not found in simulated network")


def make_client(**kwargs: object) -> httpx.Client:
    """Build an httpx client bound to the simulated network."""
    return httpx.Client(transport=httpx.MockTransport(mock_transport), **kwargs)  # type: ignore[arg-type]
