"""Capstone 16.3 [mid] — SSRF Bunker.

Harden a webhook-tester fetcher against SSRF, layer by layer, over a
simulated adversary network. See README.md for the contract.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class Control(str, Enum):
    """The gauntlet layers, in composition order."""

    SCHEME_ALLOWLIST = "scheme-allowlist"
    HOST_ALLOWLIST = "host-allowlist"
    IP_RANGE_DENY = "ip-range-deny"
    DNS_PINNING = "dns-pinning"
    REDIRECT_REVALIDATION = "redirect-revalidation"
    SIZE_CAP = "size-cap"
    EGRESS_RULES = "egress-rules"


class SsrfBlocked(Exception):
    """Raised when a control layer refuses the fetch. Carries the layer."""

    def __init__(self, layer: Control, url: str) -> None:
        super().__init__(f"blocked by {layer.value}: {url}")
        self.layer = layer


@dataclass(frozen=True)
class FetchResult:
    url: str
    status: int
    body_bytes: int


def naive_fetch(url: str, network: "object") -> FetchResult:
    """The vulnerable fetcher: follows redirects, no checks. The exploit target."""
    raise NotImplementedError("TODO: implement naive_fetch")


class SafeFetcher:
    """The hardened fetcher. Controls compose; each can refuse the fetch.

    TODO: enable layers incrementally; resolve DNS once and pin it;
    re-validate every redirect hop against the full policy; cap body size.
    """

    def __init__(self, network: "object", controls: frozenset[Control]) -> None:
        self.network = network
        self.controls = controls

    def fetch(self, url: str) -> FetchResult:
        raise NotImplementedError("TODO: implement SafeFetcher.fetch")


def exploit_metadata_ip(network: "object") -> FetchResult:
    """Exploit 1: fetch the link-local metadata endpoint (169.254.169.254)."""
    raise NotImplementedError("TODO: implement exploit_metadata_ip")


def exploit_internal_host(network: "object") -> FetchResult:
    """Exploit 2: reach an internal-only hostname."""
    raise NotImplementedError("TODO: implement exploit_internal_host")


def exploit_redirect_chain(network: "object") -> FetchResult:
    """Exploit 3: public URL that redirects twice into link-local space."""
    raise NotImplementedError("TODO: implement exploit_redirect_chain")


def blame_table() -> dict[Control, list[str]]:
    """Layer-by-layer: which control stops which exploit.

    Contract: includes the layers that stop nothing alone but matter in
    composition (documented as such).
    """
    raise NotImplementedError("TODO: implement blame_table")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ssrf-bunker", description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("DRY RUN: run 3 exploits against naive fetcher, then the layered SafeFetcher")
        return 0
    print("Scaffold ready. Implement the TODO items in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
