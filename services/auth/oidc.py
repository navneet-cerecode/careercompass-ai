"""Strict provider-neutral OIDC access-token verification."""

from typing import Protocol

import jwt
from pydantic import ValidationError

from models.identity import VerifiedIdentity

SOLARA_IDENTITY_NAMESPACE = "urn:solarahire:identity"


class TokenValidationError(ValueError):
    """Safe signal for any rejected access token."""


class SigningKey(Protocol):
    key: object


class SigningKeyResolver(Protocol):
    def get_signing_key_from_jwt(self, token: str) -> SigningKey: ...


class OIDCTokenVerifier:
    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        jwks_url: str,
        jwks_cache_seconds: int,
        http_timeout_seconds: int,
        key_resolver: SigningKeyResolver | None = None,
    ) -> None:
        self.issuer = issuer
        self.audience = audience
        self.key_resolver = key_resolver or jwt.PyJWKClient(
            jwks_url,
            cache_keys=True,
            cache_jwk_set=True,
            lifespan=jwks_cache_seconds,
            timeout=http_timeout_seconds,
        )

    def verify(self, token: str) -> VerifiedIdentity:
        try:
            signing_key = self.key_resolver.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
                options={
                    "require": ["aud", "exp", "iat", "iss", "sub"],
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_iss": True,
                    "verify_aud": True,
                },
            )
            verified_claim = claims.get(
                f"{SOLARA_IDENTITY_NAMESPACE}:email_verified",
                claims.get("email_verified"),
            )
            if verified_claim is not True:
                raise TokenValidationError("Access token email is not verified.")
            email = claims.get(
                f"{SOLARA_IDENTITY_NAMESPACE}:email",
                claims.get("email"),
            )
            if not isinstance(email, str) or not email:
                raise TokenValidationError("Access token has no verified email.")
            name = claims.get(
                f"{SOLARA_IDENTITY_NAMESPACE}:name",
                claims.get("name"),
            )
            if not isinstance(name, str) or not name.strip():
                name = email.split("@", 1)[0]
            return VerifiedIdentity(
                issuer=str(claims["iss"]),
                subject=str(claims["sub"]),
                email=email,
                name=name,
            )
        except TokenValidationError:
            raise
        except (jwt.PyJWTError, jwt.PyJWKClientError, ValidationError, ValueError) as error:
            raise TokenValidationError("Access token is invalid.") from error
