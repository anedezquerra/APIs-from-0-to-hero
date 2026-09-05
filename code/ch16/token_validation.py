"""Token validation middleware: JWKS-style key resolution, scope/audience
enforcement, and claim-to-principal mapping.

Validation order is a security invariant: never trust a claim before the
signature, issuer, audience, and expiry have all been verified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ALLOWED_ALGORITHMS = ("RS256",)  # allow-list: 'none' and HS-confusion rejected
CLOCK_LEEWAY_SECONDS = 30


@dataclass(frozen=True)
class Principal:
    """The authenticated caller, mapped from verified claims only."""

    subject: str
    tenant: str
    scopes: frozenset[str] = field(default_factory=frozenset)
    roles: frozenset[str] = field(default_factory=frozenset)

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes

    def require_scope(self, scope: str) -> None:
        if not self.has_scope(scope):
            raise HTTPException(
                status_code=403,
                detail=f"missing required scope '{scope}'",
                headers={"WWW-Authenticate": f'Bearer scope="{scope}"'},
            )


class TokenValidator:
    """Verifies Bearer tokens against a JWKS-style key map."""

    def __init__(
        self,
        jwks: Mapping[str, str],
        *,
        issuer: str,
        audience: str,
        leeway: int = CLOCK_LEEWAY_SECONDS,
    ) -> None:
        if not jwks:
            raise ValueError("JWKS key map must not be empty")
        self._jwks = dict(jwks)
        self._issuer = issuer
        self._audience = audience
        self._leeway = leeway

    def validate(self, token: str) -> Principal:
        header = self._unverified_header(token)
        key = self._resolve_key(header)
        claims = self._verify_claims(token, key)
        return self._to_principal(claims)

    def _unverified_header(self, token: str) -> dict[str, Any]:
        try:
            return jwt.get_unverified_header(token)
        except jwt.DecodeError as exc:
            raise HTTPException(status_code=401, detail="malformed token") from exc

    def _resolve_key(self, header: dict[str, Any]) -> str:
        alg = header.get("alg")
        if alg not in ALLOWED_ALGORITHMS:
            raise HTTPException(status_code=401, detail="disallowed algorithm")
        kid = header.get("kid")
        key = self._jwks.get(kid) if isinstance(kid, str) else None
        if key is None:
            # Real deployments: one rate-limited JWKS refetch, then fail.
            raise HTTPException(status_code=401, detail="unknown key id")
        return key

    def _verify_claims(self, token: str, key: str) -> dict[str, Any]:
        try:
            claims: dict[str, Any] = jwt.decode(
                token,
                key,
                algorithms=list(ALLOWED_ALGORITHMS),
                audience=self._audience,
                issuer=self._issuer,
                leeway=self._leeway,
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(status_code=401, detail="token expired") from exc
        except jwt.InvalidTokenError as exc:
            raise HTTPException(status_code=401, detail="invalid token") from exc
        return claims

    @staticmethod
    def _to_principal(claims: dict[str, Any]) -> Principal:
        scope_claim = claims.get("scope", "")
        if not isinstance(scope_claim, str):
            raise HTTPException(status_code=401, detail="malformed scope claim")
        roles_claim = claims.get("roles", [])
        if not isinstance(roles_claim, list):
            raise HTTPException(status_code=401, detail="malformed roles claim")
        tenant = claims.get("tenant")
        if not isinstance(tenant, str) or not tenant:
            raise HTTPException(status_code=401, detail="missing tenant claim")
        return Principal(
            subject=str(claims["sub"]),
            tenant=tenant,
            scopes=frozenset(s for s in scope_claim.split() if s),
            roles=frozenset(str(r) for r in roles_claim),
        )


def build_auth_dependency(
    validator: TokenValidator,
) -> Any:
    """Wire a TokenValidator into FastAPI's dependency system."""
    bearer = HTTPBearer(auto_error=True)

    def current_principal(
        credentials: HTTPAuthorizationCredentials = Depends(bearer),
    ) -> Principal:
        return validator.validate(credentials.credentials)

    return current_principal


def demo_app(validator: TokenValidator) -> FastAPI:
    """Minimal app proving scope enforcement end to end."""
    app = FastAPI(title="NWR Token Validation Demo")
    principal_dep = build_auth_dependency(validator)

    @app.get("/v1/whoami")
    def whoami(principal: Principal = Depends(principal_dep)) -> dict[str, Any]:
        return {
            "sub": principal.subject,
            "tenant": principal.tenant,
            "scopes": sorted(principal.scopes),
        }

    @app.get("/v1/fleet/commands")
    def fleet_commands(
        request: Request,
        principal: Principal = Depends(principal_dep),
    ) -> dict[str, Any]:
        principal.require_scope("fleet:command")
        return {"accepted": True, "by": principal.subject}

    return app
