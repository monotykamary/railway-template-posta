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

- All images are pinned by tag and immutable digest: `jkaninda/posta:0.14.0`, `ghcr.io/railwayapp-templates/postgres-ssl:18`, `redis:8.2`.
- `POSTA_JWT_SECRET`, `POSTA_ADMIN_PASSWORD`, and `POSTA_ENCRYPTION_KEY` are generated at deploy time.
- The server and worker share `POSTA_DB_URL` and `POSTA_REDIS_URL`, built from Railway's database and Redis reference variables over private networking. Do not replace these cross-service references with literal values.
- Health checks use `GET /healthz` on the Posta server.
- Database migrations run automatically when the server starts against an empty database.
- Optional: attach a Railway bucket and set the `POSTA_BLOB_S3_*` variables so attachments are shared correctly if you scale the server or worker to multiple instances.

### Why Deploy Posta on Railway?

Railway provisions PostgreSQL, Redis, and private networking in one click, scales workers independently of request traffic as your send volume grows, and gives the dashboard a managed HTTPS domain immediately. The whole stack — API, worker, database, and queue — is deployable without writing Compose files or maintaining servers.

## Limitations

- **Outbound SMTP requires a Railway Pro plan.** Railway blocks outbound SMTP ports (25, 465, 587, 2525) on Free, Trial, and Hobby plans. Posta sends only over SMTP and has no HTTPS API provider fallback, so non-Pro plans cannot complete delivery. On Pro it works unchanged.
- **No direct MX delivery.** Railway cannot expose port 25, so internet mail servers cannot deliver inbound mail directly to the deployment. Inbound SMTP is disabled by default; use an HTTP-forwarding MX provider with Posta's `/api/v1/inbound/webhook` endpoint.
- SMTP relay (port 2526) is disabled by default and intended for private networks.
