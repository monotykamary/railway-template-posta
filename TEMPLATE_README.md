# Deploy and Host Posta on Railway

Posta is a self-hosted email delivery platform that gives applications a REST API for sending, templating, and tracking email, with inbound parsing, SMTP relay, campaigns, and webhooks. This template deploys the pinned upstream image with a dedicated background worker, Railway-managed PostgreSQL 18, and Redis 8.

## About Hosting Posta

Posta runs as a single Go binary in two modes. The server serves the HTTP API on port 9000, the dashboard, and the health endpoint. The worker consumes Asynq queues from Redis to deliver email, retry failures, run campaigns, and deliver webhooks. Both modes are stateless: emails, templates, contacts, and logs live in PostgreSQL, queue state lives in Redis, and attachments and raw inbound messages stay in PostgreSQL by default or move to S3-compatible storage when blob settings are provided.

The Posta server service owns the public Railway HTTPS domain. The worker, PostgreSQL, and Redis are reachable only through Railway private networking. The first administrator is created automatically on an empty database from `POSTA_ADMIN_EMAIL` and the generated `POSTA_ADMIN_PASSWORD`; production mode refuses placeholder values, so sign in with the generated password shown in the server's variables.

## Common Use Cases

- Transactional email from your applications through your own SMTP accounts, with retries and suppression handling
- Marketing campaigns with subscriber lists, scheduling, A/B testing, and engagement analytics
- Inbound email parsing with webhook forwarding into automation pipelines
- A fully self-hosted alternative to SendGrid, Mailgun, or Postmark with complete data ownership

## Dependencies for Posta Hosting

### Deployment Dependencies

- Railway PostgreSQL 18 (`postgres-ssl`) for application state and migrations, with daily volume backups
- Railway Redis 8 for Asynq queues and the job scheduler, persisted to a volume with daily backups
- A Railway Pro plan for outbound SMTP delivery (see limitations)

### Implementation Details

- Pinned releases: `jkaninda/posta:0.20.1`, `ghcr.io/railwayapp-templates/postgres-ssl:18`, `redis:8.10.2`, each with an immutable digest.
- `POSTA_JWT_SECRET`, `POSTA_ADMIN_PASSWORD`, and `POSTA_ENCRYPTION_KEY` are generated at deploy time.
- The server and worker share `POSTA_DB_HOST`, `POSTA_DB_PORT`, `POSTA_DB_NAME`, `POSTA_DB_USER`, `POSTA_DB_PASSWORD`, and `POSTA_REDIS_URL`, built from Railway database and Redis references over private networking. Do not replace these references with literal credentials.
- Health checks use `GET /healthz` on the Posta server.
- Database migrations run automatically at startup. Back up before an upgrade; the 0.18 migration changes template names and drops the old slug columns.
- Optional: attach a Railway bucket and set the `POSTA_BLOB_S3_*` variables so attachments are shared correctly if you scale the server or worker to multiple instances.

### Why Deploy Posta on Railway?

Railway provisions PostgreSQL, Redis, and private networking in one click, scales workers independently of request traffic as your send volume grows, and gives the dashboard a managed HTTPS domain immediately. The whole stack — API, worker, database, and queue — is deployable without writing Compose files or maintaining servers.

## Forwarded-IP security policy

The template sets `POSTA_TRUSTED_PROXIES=127.0.0.1/32,::1/128` on both server and worker. This trusts only loopback peers, **not the Railway edge**. Forwarded client-IP headers are therefore ignored for Railway requests: rate limits and audit logs see the immediate proxy IP, and multiple end users can share one rate-limit bucket. Do not rely on end-client IP allowlists or per-client IP attribution with this default.

This restrictive choice avoids trusting arbitrary forwarded headers without assuming undocumented, stable Railway proxy CIDRs. Operators may supply independently verified exact proxy IPs/CIDRs if their deployment guarantees them; never use a trust-all range or invent a platform CIDR. The current upstream default (unset) trusts forwarded headers from every peer and logs an insecure-configuration warning.

Release validation uses a disposable, authenticated Mailpit inbox to prove queued worker delivery. That fixture, its credentials, and its domain are **not** part of this template or its serialized defaults. Controlled synthetic delivery does not prove deliverability to public mailbox providers.

## Upgrade and rollback precautions

Back up both PostgreSQL and Redis before upgrading and retain the generated encryption and signing secrets. The server runs database migrations at startup; the 0.18 migration changes stored template names and removes the old slug columns. Restore matching backups when rolling back rather than assuming an older binary can read the migrated schema.

During a direct 0.17-to-0.20.1 upgrade, a worker started before the server finishes migrations can briefly report that the `licenses` table is absent. The reviewed upstream worker continues and reloads license state every minute. Validation retained that one startup race, verified delivery and the original stored template/API key afterward, and required no recurrence on the subsequent exact-version redeploy. Recurring errors or failed migrations are not an accepted steady state.

## Limitations

- **Outbound SMTP requires a Railway Pro plan.** Railway blocks outbound SMTP ports (25, 465, 587, 2525) on Free, Trial, and Hobby plans. Posta sends only over SMTP and has no HTTPS API provider fallback, so non-Pro plans cannot complete delivery. On Pro it works unchanged.
- **No direct MX delivery.** Railway cannot expose port 25, so internet mail servers cannot deliver inbound mail directly to the deployment. Inbound SMTP is disabled by default; use an HTTP-forwarding MX provider with Posta's `/api/v1/inbound/webhook` endpoint.
- SMTP relay (port 2526) is disabled by default and intended for private networks.

## Source and attribution

[Railway wrapper](https://github.com/monotykamary/railway-template-posta) · [Posta upstream](https://github.com/goposta/posta) · Upstream AGPL-3.0-or-later; wrapper documentation MIT.
