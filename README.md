# Posta on Railway

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

- Posta `0.14.0` — `jkaninda/posta:0.14.0`, image index digest `sha256:8cee61195ba4359d5e3d2e4ce385ec33f368deaefdc10f9a1225aaf0a6816c0e`
- PostgreSQL — `ghcr.io/railwayapp-templates/postgres-ssl:18` (Railway-managed image), image index digest `sha256:469c779c7c57ec6bad4670a0a3cb5a830aa6e0ce4f3707137608de5223a5041c`
- Redis — `redis:8.2`, image index digest `sha256:7d1e4ce8b9395088377ab382d1f6cfdbd13b3690795198a0399ab8d683064d6d`
- Railway-managed PostgreSQL and Redis volumes carry daily backup schedules

All images are pinned by tag and immutable digest. Updating this repository does not automatically update Posta; version bumps are deliberate.

## Post-deploy setup

1. Open the Posta server's Railway HTTPS domain.
2. Sign in with `admin@example.com` and the generated `POSTA_ADMIN_PASSWORD` variable. Production mode refuses to seed placeholder credentials, so use the generated value.
3. Change the administrator password, then create your workspace and API key.
4. Add your SMTP provider in the dashboard and verify your sending domain's SPF, DKIM, and DMARC records.
5. Optional: attach a Railway bucket and set the `POSTA_BLOB_S3_*` variables to move attachments and raw inbound messages out of the database.

`POSTA_JWT_SECRET`, `POSTA_ADMIN_PASSWORD`, and `POSTA_ENCRYPTION_KEY` are generated at deploy time. Do not replace cross-service variable references (`POSTA_DB_URL`, `POSTA_REDIS_URL`) with literal values.

## Railway-specific limitations

- **Outbound SMTP requires a Railway Pro plan.** Railway blocks outbound SMTP ports (25, 465, 587, 2525) on Free, Trial, and Hobby plans. Posta delivers email over SMTP only — it has no HTTPS API provider fallback — so on non-Pro plans the core send pipeline cannot reach your SMTP provider. On Pro it works unchanged.
- **No direct MX delivery.** Internet mail servers deliver inbound mail to port 25, which Railway's TCP proxy cannot expose. Inbound SMTP is disabled by default. To receive mail, point an HTTP-forwarding MX provider (for example Cloudflare Email Routing) at Posta's built-in webhook: `POST /api/v1/inbound/webhook` with the `X-Posta-Inbound-Secret` header matching `POSTA_INBOUND_WEBHOOK_SECRET`.
- **SMTP relay (port 2526) is off by default.** It is designed for private networks. If you enable it, expose it through a Railway TCP proxy; clients must use Railway's generated external port.

## Updating

Bump the pinned Posta tag and image digests deliberately after reviewing upstream release notes. Re-run live validation — startup against the existing database, worker processing, and an end-to-end SMTP delivery test — before publishing the update. Posta applies its own database migrations on startup.

## Sources and licensing

- [Posta source](https://github.com/goposta/posta)
- [Posta v0.14.0](https://github.com/goposta/posta/releases/tag/v0.14.0)
- [Posta documentation](https://docs.goposta.dev/)

This wrapper is MIT licensed. Posta is AGPL-3.0-or-later; the logo in `assets/` is an unchanged copy of upstream artwork and retains its upstream license. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
