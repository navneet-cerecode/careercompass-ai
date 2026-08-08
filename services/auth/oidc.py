"""Strict provider-neutral OIDC access-token verification."""

from collections.abc import Mapping
from typing import Protocol

import jwt
import requests
from pydantic import ValidationError

from models.identity import VerifiedIdentity

SOLARA_IDENTITY_NAMESPACE = "urn:solarahire:identity"


class TokenValidationError(ValueError):
    """Safe signal for any rejected access token."""


class SigningKey(Protocol):
    key: object


class SigningKeyResolver(Protocol):
    def get_signing_key_from_jwt(self, token: str) -> SigningKey: ...


class UserInfoResolver(Protocol):
    def get_user_info(self, token: str) -> Mapping[str, object]: ...


class HTTPUserInfoResolver:
    def __init__(self, url: str, timeout_seconds: int) -> None:
        self.url = url
        self.timeout_seconds = timeout_seconds

    def get_user_info(self, token: str) -> Mapping[str, object]:
        response = requests.get(
            self.url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, Mapping):
            raise TokenValidationError("OIDC UserInfo response is invalid.")
        return payload


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
        userinfo_resolver: UserInfoResolver | None = None,
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
        self.userinfo_resolver = userinfo_resolver or HTTPUserInfoResolver(
            f"{issuer.rstrip('/')}/userinfo",
            http_timeout_seconds,
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
            email = claims.get(
                f"{SOLARA_IDENTITY_NAMESPACE}:email",
                claims.get("email"),
            )
            name = claims.get(
                f"{SOLARA_IDENTITY_NAMESPACE}:name",
                claims.get("name"),
            )
            if verified_claim is None or not isinstance(email, str) or not email:
                # ponytail: this fallback is uncached; add a short-lived hash-keyed
                # cache only if UserInfo latency becomes measurable in production.
                profile = self.userinfo_resolver.get_user_info(token)
                if profile.get("sub") != claims["sub"]:
                    raise TokenValidationError("OIDC UserInfo subject does not match.")
                verified_claim = profile.get("email_verified")
                email = profile.get("email")
                name = profile.get("name", name)
            if verified_claim is not True:
                raise TokenValidationError("Access token email is not verified.")
            if not isinstance(email, str) or not email:
                raise TokenValidationError("Access token has no verified email.")
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
        except (
            jwt.PyJWTError,
            jwt.PyJWKClientError,
            requests.RequestException,
            ValidationError,
            ValueError,
        ) as error:
            raise TokenValidationError("Access token is invalid.") from error
