"""Listing 5.5 -- EDUCATIONAL ATTACK DEMO: RS256 -> HS256 algorithm confusion.

The classic JWT library bug: the verifier picks its verification ALGORITHM
from the attacker-controlled token header while picking the KEY from its own
RS256 configuration. An attacker who knows the public key (public keys are
public -- JWKS endpoints publish them) mints an ``alg=HS256`` token using
the public key bytes as the HMAC secret. The naive verifier computes
``HMAC(public_key, token)`` and the forgery verifies.

This file demonstrates the attack against a naive verifier and its failure
against a hardened one. Because the Python standard library has no RSA, we
use a TOY TEXTBOOK RSA (small fixed primes, raw ``pow`` math, no padding).
It exists ONLY to model the asymmetric/private-public key relationship --
it is not remotely secure cryptography. Use ``cryptography`` in production.

Synthetic Northwind Robotics fixtures only. Runs fully offline.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Mapping

# --- Toy textbook RSA (EDUCATIONAL STAND-IN; never use in real code) --------
_P = 1_299_709  # fixed small primes for deterministic keys
_Q = 1_299_721
N = _P * _Q
_E = 65_537
_D = pow(_E, -1, (_P - 1) * (_Q - 1))
PUBLIC_KEY_PEM = f"-----BEGIN NWR PUBLIC KEY-----\nn={N} e={_E}\n-----END NWR PUBLIC KEY-----".encode()
PRIVATE_KEY_PEM = f"-----BEGIN NWR PRIVATE KEY-----\nn={N} d={_D}\n-----END NWR PRIVATE KEY-----".encode()


def _toy_rsa_sign(signing_input: bytes) -> bytes:
    h = int.from_bytes(hashlib.sha256(signing_input).digest(), "big") % N
    return pow(h, _D, N).to_bytes((N.bit_length() + 7) // 8, "big")


def _toy_rsa_verify(signing_input: bytes, signature: bytes) -> bool:
    h = int.from_bytes(hashlib.sha256(signing_input).digest(), "big") % N
    return pow(int.from_bytes(signature, "big"), _E, N) == h


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(segment: str) -> bytes:
    return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))


def _mint(header: Mapping[str, object], payload: Mapping[str, object]) -> str:
    signing_input = (
        f"{_b64(json.dumps(header, separators=(',', ':')).encode())}."
        f"{_b64(json.dumps(payload, separators=(',', ':')).encode())}"
    ).encode("ascii")
    if header["alg"] == "RS256":  # legit IdP path: signs with PRIVATE key
        sig = _toy_rsa_sign(signing_input)
    else:  # attacker path: HMAC with the PUBLIC key as the "secret"
        sig = hmac.new(PUBLIC_KEY_PEM, signing_input, hashlib.sha256).digest()
    return signing_input.decode("ascii") + "." + _b64(sig)


CLAIMS = {"iss": "https://idp.northwind-robotics.example/", "sub": "attacker",
          "aud": "nwr-parts-api", "role": "admin", "exp": 9_999_999_999}


def naive_verify(token: str, configured_key: bytes) -> dict[str, object]:
    """BUG: trusts the token's alg header to choose the verification method,
    while the KEY comes from local config. Classic algorithm confusion."""
    header_b64, payload_b64, sig_b64 = token.split(".")
    header = json.loads(_unb64(header_b64))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = _unb64(sig_b64)
    if header["alg"] == "RS256":
        ok = _toy_rsa_verify(signing_input, signature)
    elif header["alg"] == "HS256":
        ok = hmac.compare_digest(
            hmac.new(configured_key, signing_input, hashlib.sha256).digest(), signature
        )
    else:
        ok = False
    if not ok:
        raise PermissionError("invalid signature")
    return json.loads(_unb64(payload_b64))


def hardened_verify(token: str, configured_key: bytes) -> dict[str, object]:
    """FIX: the algorithm allow-list is part of the KEY CONFIGURATION, so the
    token header can never downgrade RS256 to HS256."""
    header_b64, payload_b64, sig_b64 = token.split(".")
    header = json.loads(_unb64(header_b64))
    if header.get("alg") != "RS256":  # allow-list of exactly one algorithm
        raise PermissionError(f"algorithm not allowed: {header.get('alg')!r}")
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    if not _toy_rsa_verify(signing_input, _unb64(sig_b64)):
        raise PermissionError("invalid signature")
    return json.loads(_unb64(payload_b64))


def main() -> None:
    forged = _mint({"alg": "HS256", "typ": "JWT"}, CLAIMS)
    legit = _mint({"alg": "RS256", "typ": "JWT"},
                  {**CLAIMS, "sub": "svc-parts-cli", "role": "reader"})

    for name, verifier in (("naive   ", naive_verify), ("hardened", hardened_verify)):
        try:
            claims = verifier(legit, PUBLIC_KEY_PEM)
            print(f"[{name}] legit RS256 token     -> ACCEPTED sub={claims['sub']}")
        except PermissionError as exc:
            print(f"[{name}] legit RS256 token     -> rejected ({exc})")
        try:
            claims = verifier(forged, PUBLIC_KEY_PEM)
            print(f"[{name}] forged HS256 (confused) -> ACCEPTED!! role={claims['role']} "
                  f"<-- attack succeeded")
        except PermissionError as exc:
            print(f"[{name}] forged HS256 (confused) -> rejected ({exc}) <-- attack failed")


if __name__ == "__main__":
    main()
