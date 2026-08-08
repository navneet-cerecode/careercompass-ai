from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from services.auth.oidc import (
    SOLARA_IDENTITY_NAMESPACE,
    OIDCTokenVerifier,
    TokenValidationError,
)


class StaticSigningKey:
    def __init__(self, key):
        self.key = key


class StaticKeyResolver:
    def __init__(self, key):
        self.key = StaticSigningKey(key)

    def get_signing_key_from_jwt(self, _token):
        return self.key


class StaticUserInfoResolver:
    def __init__(self, profile):
        self.profile = profile
        self.calls = 0

    def get_user_info(self, _token):
        self.calls += 1
        return self.profile


def build_verifier_and_key():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = OIDCTokenVerifier(
        issuer="https://identity.example.test/",
        audience="urn:solarahire:api",
        jwks_url="https://identity.example.test/.well-known/jwks.json",
        jwks_cache_seconds=300,
        http_timeout_seconds=5,
        key_resolver=StaticKeyResolver(private_key.public_key()),
    )
    return verifier, private_key


def encode_token(private_key, **overrides):
    now = datetime.now(UTC)
    claims = {
        "iss": "https://identity.example.test/",
        "sub": "provider-user-123",
        "aud": "urn:solarahire:api",
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "email": "ada@example.com",
        "email_verified": True,
        "name": "Ada Lovelace",
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256")


def test_oidc_verifier_accepts_required_verified_claims():
    verifier, private_key = build_verifier_and_key()

    identity = verifier.verify(encode_token(private_key))

    assert identity.subject == "provider-user-123"
    assert str(identity.email) == "ada@example.com"
    assert identity.name == "Ada Lovelace"


def test_oidc_verifier_accepts_namespaced_solara_hire_identity_claims():
    verifier, private_key = build_verifier_and_key()
    token = encode_token(
        private_key,
        email=None,
        email_verified=None,
        name=None,
        **{
            f"{SOLARA_IDENTITY_NAMESPACE}:email": "ada@example.com",
            f"{SOLARA_IDENTITY_NAMESPACE}:email_verified": True,
            f"{SOLARA_IDENTITY_NAMESPACE}:name": "Ada Lovelace",
        },
    )

    identity = verifier.verify(token)

    assert str(identity.email) == "ada@example.com"
    assert identity.name == "Ada Lovelace"


def test_oidc_verifier_uses_userinfo_when_standard_access_token_omits_profile_claims():
    verifier, private_key = build_verifier_and_key()
    userinfo = StaticUserInfoResolver(
        {
            "sub": "provider-user-123",
            "email": "ada@example.com",
            "email_verified": True,
            "name": "Ada Lovelace",
        }
    )
    verifier.userinfo_resolver = userinfo

    identity = verifier.verify(
        encode_token(private_key, email=None, email_verified=None, name=None)
    )

    assert str(identity.email) == "ada@example.com"
    assert identity.name == "Ada Lovelace"
    assert userinfo.calls == 1


def test_oidc_verifier_rejects_userinfo_for_another_subject():
    verifier, private_key = build_verifier_and_key()
    verifier.userinfo_resolver = StaticUserInfoResolver(
        {
            "sub": "another-user",
            "email": "ada@example.com",
            "email_verified": True,
        }
    )

    with pytest.raises(TokenValidationError):
        verifier.verify(encode_token(private_key, email=None, email_verified=None, name=None))


@pytest.mark.parametrize(
    "overrides",
    [
        {"aud": "another-api"},
        {"iss": "https://attacker.example/"},
        {"email_verified": False},
        {"exp": datetime.now(UTC) - timedelta(seconds=1)},
    ],
)
def test_oidc_verifier_rejects_untrusted_claims(overrides):
    verifier, private_key = build_verifier_and_key()

    with pytest.raises(TokenValidationError):
        verifier.verify(encode_token(private_key, **overrides))
