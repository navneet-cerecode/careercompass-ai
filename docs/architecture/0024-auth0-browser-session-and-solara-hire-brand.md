# 0024 — Auth0 browser sessions and the Solara Hire product name

Status: Accepted

Date: 2026-08-02

## Context

The product previously used CareerCompass AI as its working name. The public product is now
Solara Hire. The verified identity boundary from ADR 0023 also needs a browser implementation
without exposing access or refresh tokens to client-side JavaScript.

## Decision

- Use **Solara Hire** on public UI, metadata, API defaults, smoke checks, and current operational
  documentation.
- Keep legacy database names, Docker volume names, queue namespaces, historical ADR wording, and
  the `CareerCompass` Python facade until a separate compatibility migration justifies changing
  them.
- Use Auth0's Next.js server SDK with an encrypted, HTTP-only session cookie.
- Mount Auth0's `/auth/*` routes through the Next.js 16 `proxy.ts` boundary.
- Request the `urn:solarahire:api` audience and `openid profile email offline_access` scopes.
- Forward API access tokens only inside same-origin Next.js route handlers. Tokens are never
  returned to React components or stored in browser local storage.
- Continue supporting anonymous resume parsing and discovery. When a verified session exists,
  attach its bearer token so FastAPI persists resumes and scopes discovery tasks to that owner.
- Read identity data from the namespaced access-token claims produced by the Auth0 Post Login
  Action, while retaining standard OIDC claim compatibility:
  - `urn:solarahire:identity:email`
  - `urn:solarahire:identity:email_verified`
  - `urn:solarahire:identity:name`

## Consequences

- Auth0 owns credentials and authentication ceremonies; Solara Hire stores no passwords,
  provider tokens, or browser sessions in PostgreSQL.
- A leaked background-task capability remains insufficient to access an authenticated task
  without the same verified owner.
- Session refresh cookies emitted while obtaining an API token are copied onto the same-origin
  route response.
- Unverified email sessions can enter the web UI but FastAPI rejects owner provisioning. The
  workspace explains that email verification and a fresh login are required.
- Production rollout must register exact HTTPS callback, logout, and web-origin URLs in Auth0.
