# 0031 — Provider-neutral subscriptions and entitlements

Status: accepted

## Decision

Keep subscription state in a dedicated owner-scoped table and resolve effective
product entitlements in the domain layer. Authentication remains responsible
only for verified identity. Payment-provider identifiers are optional metadata,
not user credentials.

Every verified account receives one idempotently created free subscription.
Inactive, incomplete, cancelled, or past-due paid subscriptions fall back to
free entitlements. The authenticated summary API is read-only until a payment
provider, webhook signature policy, checkout URLs, and customer portal are
configured and tested.

This establishes stable plan contracts without pretending that checkout is
available or coupling core features to Stripe-specific objects.
