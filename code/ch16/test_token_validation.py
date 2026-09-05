"""Tests for the token validation middleware and claim->principal mapping."""

from __future__ import annotations

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from jwks_fixture import (
    AUDIENCE,
    ISSUER,
    JWKS,
    SYNTHETIC_PRIVATE_PEM,
    mint_token,
)
from token_validation import TokenValidator, demo_app

VALIDATOR = TokenValidator(JWKS, issuer=ISSUER, audience=AUDIENCE)
# Tokens that must validate are minted at the current instant (now=None);
# only the expired-token test pins a past epoch. Either way every run of
# the suite exercises identical code paths and assertions.
PAST = 1_700_000_000


def test_valid_token_maps_to_principal() -> None:
    token = mint_token(
        "alice", ["fleet:read", "fleet:write"], now=None,
        extra={"roles": ["owner"]},
    )
    principal = VALIDATOR.validate(token)
    assert principal.subject == "alice"
    assert principal.tenant == "tenant-nwr"
    assert principal.has_scope("fleet:read")
    assert not principal.has_scope("admin:users")


def test_expired_token_rejected() -> None:
    token = mint_token("alice", ["fleet:read"], now=PAST, ttl_seconds=60)
    with pytest.raises(HTTPException) as err:
        VALIDATOR.validate(token)
    assert err.value.status_code == 401


def test_wrong_audience_rejected() -> None:
    token = mint_token("alice", ["fleet:read"], now=None, audience="nwr-billing-api")
    with pytest.raises(HTTPException) as err:
        VALIDATOR.validate(token)
    assert err.value.status_code == 401


def test_wrong_issuer_rejected() -> None:
    token = mint_token(
        "alice", ["fleet:read"], now=None, issuer="https://evil.example"
    )
    with pytest.raises(HTTPException) as err:
        VALIDATOR.validate(token)
    assert err.value.status_code == 401


def test_alg_none_rejected() -> None:
    import time

    issued = int(time.time())
    token = jwt.encode(
        {"iss": ISSUER, "aud": AUDIENCE, "sub": "alice", "exp": issued + 300,
         "iat": issued, "scope": "fleet:read", "tenant": "tenant-nwr"},
        key=None,
        algorithm="none",
    )
    with pytest.raises(HTTPException) as err:
        VALIDATOR.validate(token)
    assert err.value.status_code == 401


def test_unknown_kid_rejected() -> None:
    token = mint_token("alice", ["fleet:read"], now=None, kid="nwr-rotated-2099")
    with pytest.raises(HTTPException) as err:
        VALIDATOR.validate(token)
    assert err.value.status_code == 401
    assert err.value.detail == "unknown key id"


def test_tampered_signature_rejected() -> None:
    token = mint_token("alice", ["fleet:read"], now=None)
    head, payload, _sig = token.split(".")
    tampered = f"{head}.{payload}.AAAA{token.split('.')[2][4:]}"
    with pytest.raises(HTTPException):
        VALIDATOR.validate(tampered)


def test_scope_enforcement_end_to_end() -> None:
    client = TestClient(demo_app(VALIDATOR))
    reader = mint_token("alice", ["fleet:read"], now=None)
    commander = mint_token("bob", ["fleet:command"], now=None)
    assert client.get(
        "/v1/fleet/commands", headers={"Authorization": f"Bearer {reader}"}
    ).status_code == 403
    response = client.get(
        "/v1/fleet/commands", headers={"Authorization": f"Bearer {commander}"}
    )
    assert response.status_code == 200
    assert response.json()["by"] == "bob"
    assert client.get("/v1/whoami").status_code == 401  # no header at all


def test_validator_requires_nonempty_jwks() -> None:
    with pytest.raises(ValueError):
        TokenValidator({}, issuer=ISSUER, audience=AUDIENCE)


def test_minted_key_fixture_is_self_consistent() -> None:
    # Guards the fixture itself: the synthetic keypair must sign/verify.
    token = jwt.encode({"sub": "selftest"}, SYNTHETIC_PRIVATE_PEM, algorithm="RS256")
    decoded = jwt.decode(
        token, next(iter(JWKS.values())), algorithms=["RS256"]
    )
    assert decoded["sub"] == "selftest"
