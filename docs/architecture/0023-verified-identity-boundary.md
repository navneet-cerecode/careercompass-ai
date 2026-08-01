# ADR 0023: Verified external identity boundary

- Status: Accepted
- Date: 2026-08-02

## Context

CareerCompass already stores owner-scoped resumes, searches, saved jobs, applications, and
background tasks, but no HTTP request has a verified user identity. Adding passwords to this
repository would create credential-storage, reset, breach-response, and multi-factor
authentication responsibilities that are unrelated to career intelligence.

Email alone is not a safe account-linking key. Provider tokens and refresh tokens must not be
stored in product tables or passed through Redis.

## Decision

Use a provider-neutral OpenID Connect access-token boundary:

- FastAPI accepts bearer access tokens only when `AUTH_ISSUER`, `AUTH_AUDIENCE`, and
  `AUTH_JWKS_URL` are configured.
- Tokens must use `RS256` and pass signature, issuer, audience, expiry, issued-at, and subject
  validation.
- Initial provisioning additionally requires an email claim with `email_verified=true`.
- Every rejection returns one generic machine code; raw tokens, claims, signing errors, and JWKS
  responses are never logged or returned.
- Missing authentication remains allowed only on routes explicitly participating in the
  anonymous compatibility rollout.

External identities live in `user_identities`, linked to the credential-free `users` profile.
The unique identity key is `(issuer, subject)`. A matching email does not automatically link a
new identity; it returns `identity_link_required` for a future reviewed linking flow.

Authenticated resume parsing stores an immutable owner-scoped version. Authenticated job
discovery stores the verified `user_id`, and task delivery carries only task and user UUIDs.
Polling and cancellation require both the opaque task capability and the same principal.

The canonical Next.js product remains anonymous-compatible in Phase 6A. Provider-specific login,
callback, refresh-token, logout, and secure server-session UI belong to Phase 6B after the
identity vendor and deployment origin are selected. No placeholder or nonfunctional sign-in UI
is added.

## Consequences

- CareerCompass stores no passwords, OIDC access tokens, or refresh tokens.
- One user can support multiple providers in a future explicit linking flow.
- Existing legacy users are not silently merged by email.
- Direct API clients can use the authenticated ownership boundary immediately.
- The current browser workspace remains functional while the provider-specific session adapter is
  implemented and tested separately.
