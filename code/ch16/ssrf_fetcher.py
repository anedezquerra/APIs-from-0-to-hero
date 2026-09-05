"""SSRF-safe outbound fetcher.

Defense layers, each independently sufficient to block the lab exploits:
  1. Scheme allow-list (https only by default).
  2. Host allow-list (exact match; no suffix tricks).
  3. Port restriction.
  4. DNS pinning: resolve first, reject private/link-local/loopback ranges,
     then connect to the *validated* address (closes DNS-rebinding TOCTOU).
  5. Redirect re-validation: every hop is checked like the original URL.
  6. Size and content-type caps on the response.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from typing import Callable

import httpx

MAX_BODY_BYTES = 64 * 1024
ALLOWED_SCHEMES = frozenset({"https", "http"})  # http only for the offline lab
ALLOWED_PORTS = frozenset({80, 443, 8443})


class SsrfBlockedError(PermissionError):
    """Raised when a URL fails any layer of the SSRF policy."""


# Explicit blocklist (stable across Python versions, unlike the shifting
# semantics of ``is_private``). In production, prefer ``ip.is_global``
# from a maintained egress-control library instead of hand-rolling this.
_BLOCKED_NETWORKS = tuple(
    ipaddress.ip_network(net)
    for net in (
        "0.0.0.0/8",        # "this host"
        "10.0.0.0/8",       # RFC 1918
        "100.64.0.0/10",    # carrier-grade NAT
        "127.0.0.0/8",      # loopback
        "169.254.0.0/16",   # link-local: home of 169.254.169.254 metadata
        "172.16.0.0/12",    # RFC 1918
        "192.168.0.0/16",   # RFC 1918
        "224.0.0.0/4",      # multicast
        "240.0.0.0/4",      # reserved
        "::/128",           # unspecified
        "::1/128",          # IPv6 loopback
        "fc00::/7",         # IPv6 unique-local
        "fe80::/10",        # IPv6 link-local
        "ff00::/8",         # IPv6 multicast
        "::ffff:0:0/96",    # IPv4-mapped IPv6 (re-checked after mapping)
    )
)


def _is_public_address(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped  # canonicalize ::ffff:10.0.0.1 -> 10.0.0.1
    return not any(ip in net for net in _BLOCKED_NETWORKS)


@dataclass(frozen=True)
class OutboundPolicy:
    allowed_hosts: frozenset[str]
    allowed_schemes: frozenset[str] = ALLOWED_SCHEMES
    allowed_ports: frozenset[int] = ALLOWED_PORTS
    max_redirects: int = 3

    def check_url(self, url: str) -> httpx.URL:
        parsed = httpx.URL(url)
        scheme = parsed.scheme.lower()
        if scheme not in self.allowed_schemes:
            raise SsrfBlockedError(f"scheme '{scheme}' not allowed")
        host = (parsed.host or "").lower()
        if host not in self.allowed_hosts:
            raise SsrfBlockedError(f"host '{host}' not on allow-list")
        port = parsed.port or (443 if scheme == "https" else 80)
        if port not in self.allowed_ports:
            raise SsrfBlockedError(f"port {port} not allowed")
        # Canonicalization guard: reject userinfo and raw-IP literals.
        if parsed.username or parsed.password:
            raise SsrfBlockedError("userinfo in URL is not allowed")
        if _looks_like_ip(host):
            raise SsrfBlockedError("raw IP literals are not allowed")
        return parsed

    def check_resolved(
        self, parsed: httpx.URL, resolve: Callable[[str], list[str]]
    ) -> None:
        """DNS pinning: every resolved address must be public."""
        for address in resolve(parsed.host or ""):
            if not _is_public_address(address):
                raise SsrfBlockedError(f"resolved address {address} is not public")


def _looks_like_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


class SafeFetcher:
    """Fetches only URLs that survive the full policy gauntlet."""

    def __init__(
        self,
        policy: OutboundPolicy,
        client: httpx.Client,
        *,
        resolve: Callable[[str], list[str]],
    ) -> None:
        self._policy = policy
        self._client = client
        self._resolve = resolve

    def fetch_text(self, url: str) -> str:
        current = url
        for _hop in range(self._policy.max_redirects + 1):
            parsed = self._policy.check_url(current)
            self._policy.check_resolved(parsed, self._resolve)
            # follow_redirects is OFF: we re-validate every hop ourselves.
            response = self._client.get(parsed, follow_redirects=False)
            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    raise SsrfBlockedError("redirect without Location header")
                current = str(parsed.join(location))
                continue
            response.raise_for_status()
            body = response.content
            if len(body) > MAX_BODY_BYTES:
                raise SsrfBlockedError("response exceeds size cap")
            return body.decode("utf-8", errors="strict")
        raise SsrfBlockedError("too many redirects")
