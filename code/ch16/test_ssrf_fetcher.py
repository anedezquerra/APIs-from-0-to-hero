"""Tests for the SSRF-safe outbound fetcher against the simulated network."""

from __future__ import annotations

import pytest

from fake_network import make_client, simulated_dns
from ssrf_fetcher import OutboundPolicy, SafeFetcher, SsrfBlockedError

POLICY = OutboundPolicy(
    allowed_hosts=frozenset({"telemetry.partner-nwr.example"})
)


def _fetcher() -> SafeFetcher:
    return SafeFetcher(POLICY, make_client(), resolve=simulated_dns)


def test_allowed_host_fetches() -> None:
    body = _fetcher().fetch_text("https://telemetry.partner-nwr.example/v1/manifest")
    assert "firmware" in body


def test_metadata_ip_blocked_by_host_allowlist() -> None:
    with pytest.raises(SsrfBlockedError):
        _fetcher().fetch_text("http://169.254.169.254/latest/meta-data")


def test_internal_host_blocked() -> None:
    with pytest.raises(SsrfBlockedError):
        _fetcher().fetch_text("http://inventory.internal.nwr/status")


def test_scheme_restriction_blocks_file_and_gopher() -> None:
    with pytest.raises(SsrfBlockedError):
        _fetcher().fetch_text("file:///etc/passwd")
    with pytest.raises(SsrfBlockedError):
        _fetcher().fetch_text("gopher://telemetry.partner-nwr.example/")


def test_userinfo_trick_blocked() -> None:
    with pytest.raises(SsrfBlockedError):
        _fetcher().fetch_text(
            "http://telemetry.partner-nwr.example@169.254.169.254/latest"
        )


def test_dns_rebinding_blocked_when_host_resolves_private() -> None:
    fetcher = SafeFetcher(
        POLICY,
        make_client(),
        resolve=lambda host: ["10.20.0.14"],  # rebind: good name, bad address
    )
    with pytest.raises(SsrfBlockedError):
        fetcher.fetch_text("https://telemetry.partner-nwr.example/v1/manifest")


def test_redirect_target_is_revalidated() -> None:
    policy = OutboundPolicy(
        allowed_hosts=frozenset(
            {"telemetry.partner-nwr.example", "short.partner-nwr.example"}
        )
    )
    fetcher = SafeFetcher(policy, make_client(), resolve=simulated_dns)
    # short.partner-nwr.example 302s to the metadata endpoint: the hop is
    # re-validated and blocked even though the *first* URL was allowed.
    with pytest.raises(SsrfBlockedError):
        fetcher.fetch_text("https://short.partner-nwr.example/x")
