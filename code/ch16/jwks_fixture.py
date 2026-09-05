"""Local JWKS-style fixture: synthetic RSA keys + token minting for tests.

The key below is a SYNTHETIC teaching fixture generated for this workbook.
It protects nothing, signs only test tokens, and must never be deployed.
"""

from __future__ import annotations

import time
from typing import Any

import jwt

ISSUER = "https://id.northwind-robotics.example"
AUDIENCE = "nwr-fleet-api"
KEY_ID = "nwr-demo-2026-01"

SYNTHETIC_PRIVATE_PEM = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCh/+W8y3oqhIdS
2pI3BHb1vJwcD1T3StnITyGpBxlZGh39711Ql5g1ie0FMbTVEad1kLHDZFAAVnFa
lWrWyEFxYLRzlZP9+zSan30hj4BRwsvIfWGO8i9f4SaUeWk+FE+JhsxETpZwPVw9
+++i0QfEIQK5Z0XY39kOlP79ewIo+TNJV6j3q0ar4sDvwVgu9K1z+LL2JHZ6PKXI
HQ4iN9wdAMbDy0AzgEDlz+kqX8UV2o95chIh1HbH0+/XsNKPITNri/p8pSgtuHeh
jGChkb1xi82MEC1SpnHwDuBqMZmzslMKbsplHjSPZBRwbXZRNPB+FunHOgJs4H4C
LI1FwyqpAgMBAAECggEABmhTjb+d7I+YYKUSMnM5Qf1R+WQmhVokZLazNfcjarGh
7Q4qKoq3HlWpwSesUjR5Y1OJTG6rzA+fOn4oHyha5PahEeShLrhgZhtCfPDVmlDy
SX2ivbTY6IRvHQvzpzJwy5eVfcApVXV/2q3GgTHztNoPZwZC2NH7HlyzUehVzLQF
KqFV+/3waevnx+GTEkCikO4fBHHQ6sv4MgpOhuIJTF+u6xb1uAC0zoo8bimVVd9/
rKOK5ZbTZpKmPbgCv6NCzTDYeAv+vwpEz5qtSluiyUsUd3z6SLwL+nyCJDMdc84G
anXuqCLxKgKPVTeM4FYdh0W0RR/9kDvL/1KE7AEazwKBgQDPe9h+QAFtnPsnWyW9
OSM2eRUvOAKkVDLY9FYnklPeNadNywM0y/sf9MwbNFNoIb5lym/escXL0Byr4fMj
XCLvFgxQd9YLpsU8JGTZG5WOqaPND5IL9zF85k1t9y7yP/HQrF6KLMkymh2j12gg
IvCNLIQlYCRGFu46VoJ3DwttJwKBgQDH4VSjx7gpKmTfTxy4lq0n4k/oa8zJWQ78
WIq3gEfJUsjksOWXqZSvgkCX+5xBWs2LwRfPJr1XOt37HyVAwWLsxblOpPNPhCq7
tQlrE8s/9JuirMZg67Haohv65bXN9av6fiih/BiBJeiJFEA0TRSvKQa0yF6qyKs3
oGuyQDIrrwKBgQCyvMSWlfrk+6vcjoenR7aO8aYPRFf6SlJ3VZ12f3biYSQcPvwn
GmXedJr0AJKtjQwhUlAm7swvNLvOUlqLJo8tmbfIBkQNS4BzvAJoiXvAJ2FlgLlW
t38ZUqh3R85YgD+HfUYAEG7Oubc48pLPxGmnpCa+r+DvxEc7WFURzZMRVwKBgH4H
w2Gdra4vL/lqHbb6MuZCGZZ4WmDeycctYRIBTcJQc6FXNP0jDUB5BZePK+A9i/tB
3mxcheh5krwj0E57YY/fwE8pTM1njbZbmTut+Gs0Jeo1vMQh+TvdGX1i1/asoCrK
3337wcu1BmFgpncT3yXu3W6iJKbU7ridayqyta+7AoGAMfYURmN+K4jEoZbzA/Ap
lVRy9JmQUzE/UtA8QcK1VvZzn6ESUNe1G9gN6cR8HNVRZi1qaSCvgZzft3e7eQ2A
zfFTHQzFM9qTLeUlvwLFOIMMxuUBy/m4xY01vjJCiS4h/IkuKqxGbgSzUL270rGY
8KUnb5+M+Z5JoWmaVNItxcw=
-----END PRIVATE KEY-----"""

SYNTHETIC_PUBLIC_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAof/lvMt6KoSHUtqSNwR2
9bycHA9U90rZyE8hqQcZWRod/e9dUJeYNYntBTG01RGndZCxw2RQAFZxWpVq1shB
cWC0c5WT/fs0mp99IY+AUcLLyH1hjvIvX+EmlHlpPhRPiYbMRE6WcD1cPfvvotEH
xCECuWdF2N/ZDpT+/XsCKPkzSVeo96tGq+LA78FYLvStc/iy9iR2ejylyB0OIjfc
HQDGw8tAM4BA5c/pKl/FFdqPeXISIdR2x9Pv17DSjyEza4v6fKUoLbh3oYxgoZG9
cYvNjBAtUqZx8A7gajGZs7JTCm7KZR40j2QUcG12UTTwfhbpxzoCbOB+AiyNRcMq
qQIDAQAB
-----END PUBLIC KEY-----"""

# JWKS-style resolution table: kid -> verification material. A real service
# loads this from the IdP's JWKS endpoint and refreshes on unknown kid.
JWKS: dict[str, str] = {KEY_ID: SYNTHETIC_PUBLIC_PEM}


def mint_token(
    subject: str,
    scopes: list[str],
    *,
    audience: str = AUDIENCE,
    issuer: str = ISSUER,
    ttl_seconds: int = 300,
    kid: str = KEY_ID,
    tenant: str = "tenant-nwr",
    now: int | None = None,
    algorithm: str = "RS256",
    extra: dict[str, Any] | None = None,
) -> str:
    """Mint a signed JWT for tests. ``now`` is injectable for determinism."""
    issued = int(time.time()) if now is None else now
    claims: dict[str, Any] = {
        "iss": issuer,
        "aud": audience,
        "sub": subject,
        "scope": " ".join(scopes),
        "tenant": tenant,
        "iat": issued,
        "nbf": issued - 1,
        "exp": issued + ttl_seconds,
    }
    if extra:
        claims.update(extra)
    return jwt.encode(
        claims,
        SYNTHETIC_PRIVATE_PEM,
        algorithm=algorithm,
        headers={"kid": kid},
    )
