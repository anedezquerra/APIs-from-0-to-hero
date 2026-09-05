"""Listing 5.4 -- Token cache with single-flight proactive refresh and
redaction-safe logging.

``TokenCache`` guarantees three production properties:
  * proactive refresh -- tokens are renewed ``skew`` seconds BEFORE expiry,
    so in-flight requests never ride a token into its death window;
  * single-flight -- no matter how many threads hit an expired cache at
    once, exactly ONE refresh call reaches the token endpoint;
  * fail-closed -- a refresh error propagates; a poisoned cache never
    serves a known-dead token as fresh.

``RedactionFilter`` is a ``logging.Filter`` that scrubs bearer tokens,
client secrets, and API keys from every record -- install it on the root
logger before any code can log a credential.

Deterministic: the clock is injected. Synthetic Northwind Robotics fixtures
only; no network access.
"""

from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass
from typing import Callable

REDACTION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
        r"(api[_-]?key|client[_-]?secret|access[_-]?token|refresh[_-]?token)"
        r"[\"'=:\s]+[^\s\"',}]+[\"']?",
    )
)


class RedactionFilter(logging.Filter):
    """Drop-in logging filter that redacts credential-shaped substrings."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._scrub(record.getMessage())
        record.args = ()
        return True

    @staticmethod
    def _scrub(text: str) -> str:
        for pattern in REDACTION_PATTERNS:
            text = pattern.sub("[REDACTED]", text)
        return text


@dataclass(frozen=True)
class Token:
    access_token: str
    refresh_token: str
    expires_at: float  # epoch seconds


class TokenCache:
    def __init__(
        self,
        fetch: Callable[[], Token],
        refresh: Callable[[str], Token],
        now: Callable[[], float],
        skew: float = 60.0,
    ) -> None:
        self._fetch = fetch
        self._refresh = refresh
        self._now = now
        self._skew = skew
        self._lock = threading.Lock()
        self._token: Token | None = None
        self.refresh_calls = 0  # instrumentation for tests/demos

    def get(self) -> str:
        token = self._token
        if token is not None and not self._expiring_soon(token):
            return token.access_token          # fast path: no lock
        with self._lock:
            token = self._token
            if token is not None and not self._expiring_soon(token):
                return token.access_token      # double-checked under lock
            self.refresh_calls += 1            # single-flight: one call only
            self._token = (
                self._refresh(token.refresh_token) if token else self._fetch()
            )
            return self._token.access_token

    def _expiring_soon(self, token: Token) -> bool:
        return self._now() >= token.expires_at - self._skew


def main() -> None:
    # --- Redaction demo -------------------------------------------------------
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.addFilter(RedactionFilter())
    root.addHandler(handler)
    log = logging.getLogger("nwr.demo")

    # --- Deterministic clock and token factory --------------------------------
    state = {"now": 1_000.0, "counter": 0}

    def make_token(kind: str) -> Token:
        state["counter"] += 1
        return Token(
            access_token=f"at-{kind}-{state['counter']:02d}-nwr-synthetic",
            refresh_token=f"rt-{kind}-{state['counter']:02d}-nwr-synthetic",
            expires_at=state["now"] + 300.0,
        )

    cache = TokenCache(
        fetch=lambda: make_token("initial"),
        refresh=lambda rt: make_token("refresh"),
        now=lambda: state["now"],
        skew=60.0,
    )

    # 1. First call fetches; second call is served from the cache.
    first, second = cache.get(), cache.get()
    print(f"[1] cached reuse: {first == second} ({first})")

    # 2. Advance into the proactive-refresh window: expiry-59s <= now.
    state["now"] += 300.0 - 59.0
    third = cache.get()
    print(f"[2] proactive refresh fired: {third != first} ({third})")

    # 3. Single-flight: expire, then hammer the cache from 8 threads.
    state["now"] += 300.0 - 30.0
    before = cache.refresh_calls
    results: list[str] = []
    threads = [threading.Thread(target=lambda: results.append(cache.get()))
               for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"[3] threads=8 distinct tokens={len(set(results))} "
          f"refresh calls made={cache.refresh_calls - before}")

    # 4. Redaction: this must NOT print the credential.
    log.warning("retrying with Bearer at-refresh-03-nwr-synthetic after 401")
    log.info("config client_secret='nwr-super-secret-fixture' loaded")


if __name__ == "__main__":
    main()
