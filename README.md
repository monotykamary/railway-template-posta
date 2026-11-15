# Posta on Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/posta?referralCode=ZqgrJ0)

A Railway deployment of [Posta](https://github.com/goposta/posta), a self-hosted email delivery platform — a REST send API, templates, campaigns, tracking, and webhooks with a Vue dashboard — deployed with a dedicated background worker, Railway-managed PostgreSQL 18, and Redis 8.

![Posta](assets/posta-icon.png)

## What this deploys

| Service | Role | Public access |
|---|---|---|
| Posta server | HTTP API on port 9000, dashboard, `GET /healthz` | Railway HTTPS domain |
| Posta worker | Asynq consumer: delivery, retries, campaigns, scheduled jobs, webhook fan-out | Private only |
| Railway PostgreSQL 18 | Emails, templates, contacts, subscribers, logs, migrations | Private only |
| Railway Redis 8 | Asynq queues and scheduler state | Private only |

The server and worker are stateless and share all state through PostgreSQL and Redis, matching upstream's recommended production layout. No custom Dockerfiles or process adapters are needed: Posta is fully configured through environment variables, so every service uses an official image.

## Pinned versions

- Posta `0.20.1` — `jkaninda/posta:0.20.1`, image index digest `sha256:dad937819b5828ef5f1ee8a8dc54e6932e36111681da4d850522c7790d0b493b`
- PostgreSQL — `ghcr.io/railwayapp-templates/postgres-ssl:18` (Railway-managed image), image index digest `sha256:3b8bc16ccb823c9a293b09d20d4180049502ee2b243b5989d59e258450044e22` (unchanged from the published template)
- Redis — `redis:8.10.2`, image index digest `sha256:97ec88159e6d7cfb5ddef9015386087d58a912de80112f06ebdfa78fa5989901` (unchanged from the published template)
- Railway-managed PostgreSQL and Redis volumes carry daily backup schedules

All images are pinned by tag and immutable digest. Updating this repository does not automatically update Posta; version bumps are deliberate.

## Post-deploy setup

1. Open the Posta server's Railway HTTPS domain.
2. Sign in with `admin@example.com` and the generated `POSTA_ADMIN_PASSWORD` variable. Production mode refuses to seed placeholder credentials, so use the generated value.
3. Change the administrator password, then create your workspace and API key.
4. Add your SMTP provider in the dashboard and verify your sending domain's SPF, DKIM, and DMARC records.
5. Optional: attach a Railway bucket and set the `POSTA_BLOB_S3_*` variables to move attachments and raw inbound messages out of the database.

`POSTA_JWT_SECRET`, `POSTA_ADMIN_PASSWORD`, and `POSTA_ENCRYPTION_KEY` are generated at deploy time. Do not replace cross-service database references (`POSTA_DB_HOST`, `POSTA_DB_PORT`, `POSTA_DB_NAME`, `POSTA_DB_USER`, `POSTA_DB_PASSWORD`) or `POSTA_REDIS_URL` with literal credentials.

## Forwarded-IP security policy

The template sets `POSTA_TRUSTED_PROXIES=127.0.0.1/32,::1/128` on both server and worker. This trusts only loopback peers, **not the Railway edge**. Forwarded client-IP headers are therefore ignored for Railway requests: rate limits and audit logs see the immediate proxy IP, and multiple end users can share one rate-limit bucket. Do not rely on end-client IP allowlists or per-client IP attribution with this default.

This restrictive choice avoids trusting arbitrary forwarded headers without assuming undocumented, stable Railway proxy CIDRs. Operators may supply independently verified exact proxy IPs/CIDRs if their deployment guarantees them; never use a trust-all range or invent a platform CIDR. The current upstream default (unset) trusts forwarded headers from every peer and logs an insecure-configuration warning.

Release validation uses a disposable, authenticated Mailpit inbox to prove queued worker delivery. That fixture, its credentials, and its domain are **not** part of this template or its serialized defaults. Controlled synthetic delivery does not prove deliverability to public mailbox providers.

## Upgrade and rollback precautions

Back up both PostgreSQL and Redis before upgrading and retain the generated encryption and signing secrets. The server runs database migrations at startup; the 0.18 migration changes stored template names and removes the old slug columns. Restore matching backups when rolling back rather than assuming an older binary can read the migrated schema.

During a direct 0.17-to-0.20.1 upgrade, a worker started before the server finishes migrations can briefly report that the `licenses` table is absent. The reviewed upstream worker continues and reloads license state every minute. Validation retained that one startup race, verified delivery and the original stored template/API key afterward, and required no recurrence on the subsequent exact-version redeploy. Recurring errors or failed migrations are not an accepted steady state.

## Railway-specific limitations

- **Outbound SMTP requires a Railway Pro plan.** Railway blocks outbound SMTP ports (25, 465, 587, 2525) on Free, Trial, and Hobby plans. Posta delivers email over SMTP only — it has no HTTPS API provider fallback — so on non-Pro plans the core send pipeline cannot reach your SMTP provider. On Pro it works unchanged.
- **No direct MX delivery.** Internet mail servers deliver inbound mail to port 25, which Railway's TCP proxy cannot expose. Inbound SMTP is disabled by default. To receive mail, point an HTTP-forwarding MX provider (for example Cloudflare Email Routing) at Posta's built-in webhook: `POST /api/v1/inbound/webhook` with the `X-Posta-Inbound-Secret` header matching `POSTA_INBOUND_WEBHOOK_SECRET`.
- **SMTP relay (port 2526) is off by default.** It is designed for private networks. If you enable it, expose it through a Railway TCP proxy; clients must use Railway's generated external port.

## Updating

Bump the pinned Posta tag and image digests deliberately after reviewing upstream release notes. Re-run live validation — startup against the existing database, worker processing, and an end-to-end SMTP delivery test — before publishing the update. Posta applies its own database migrations on startup.

## Disposable product validation

Run `python3 scripts/smoke.py` with `BASE_URL`, `SMOKE_PHASE`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD` set for an isolated test deployment. On `SMOKE_PHASE=boot`, it authenticates, creates one template, renders a known marker, and writes a private local state file. `upgrade` and `redeploy` must retrieve the same ID and content without reseeding. The check recognizes the old `name` and new `display_name` API schemas, tests rejected authentication, and records that external email delivery was not tested.

The `0.17.0` to `0.20.1` migration has passed this check on boat, including the `name`/`display_name` transition, durable database state, a pre-upgrade SQL backup, and the separate worker. This is not a public Railway HTTPS or SMTP delivery proof; those remain release gates. Keep the state file private, outside source control, until validation cleanup. Release `0.18.0` introduced Enterprise feature gating; this check uses community template/render APIs and does not activate paid functionality.

## Sources and licensing

- [Posta source](https://github.com/goposta/posta)
- [Posta v0.20.1](https://github.com/goposta/posta/releases/tag/v0.20.1)
- [Posta documentation](https://docs.goposta.dev/)

This wrapper is MIT licensed. Posta is AGPL-3.0-or-later; the logo in `assets/` is an unchanged copy of upstream artwork and retains its upstream license. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
