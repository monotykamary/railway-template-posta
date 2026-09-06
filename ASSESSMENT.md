# Railway Template Assessment: goposta/posta

Assessed 2026-09-06 against upstream v0.14.0 (published 2026-08-29).

## Decision

`publish-with-documented-limit`

## Basis

- Stable, immutable release tag `v0.14.0`; multi-arch image verified at Docker Hub (`linux/amd64` + `linux/arm64`, ~22 MB).
- Stateless application: PostgreSQL, Redis, and optional S3-compatible blob storage. No cross-service volumes, privileged access, host devices, UDP, nested Docker, or shared-memory tuning required.
- Production-grade configuration contract: required JWT secret, placeholder-resistant admin seeding, `/healthz`, embedded migrations, first-party MX-webhook adapter for inbound.
- AGPL-3.0-or-later upstream; this wrapper preserves attribution and ships the unchanged first-party logo.

## Documented limits

1. **Outbound SMTP requires Railway Pro.** Railway blocks outbound SMTP ports (25, 465, 587, 2525) on Free, Trial, and Hobby plans. Posta delivers email over SMTP only and has no HTTPS API provider fallback (verified by code search), so the core send pipeline cannot reach an SMTP provider on non-Pro plans. On Pro it works unchanged.
2. **No direct MX delivery.** Internet mail servers deliver inbound mail to port 25, which Railway's TCP proxy cannot expose. Inbound SMTP is disabled by default; the upstream generic MX-provider webhook (`POST /api/v1/inbound/webhook`, authenticated with `POSTA_INBOUND_WEBHOOK_SECRET`) is the documented adapter path.
3. **SMTP relay (:2526) stays off by default.** It is designed for private networks; optional public exposure through a Railway TCP proxy must use Railway's generated port.

## Marketplace

No Posta template existed on the Railway marketplace at assessment time (GraphQL `templateSearch("posta")` returned empty). Comparable self-hosted email platforms (useSend, Mautic) confirm category demand. Upstream maintains an official managed template on Miabi, a different platform.

## Re-validation triggers

- Upstream minor version bumps: the project is young (first releases mid-2026) with a single maintainer.
- Any change to Railway's outbound SMTP egress policy.
