# Loot Wallet production scale notes

The repository now has an account-backed Next.js client, FastAPI API, and local SQLite development setup. Accounts, wallet cards, transactions, routing, and basic analytics are connected. This is an MVP foundation; the reward catalog is sample data and the app does not connect to banks or payment networks.

## Request path

- Ship the static Next.js bundle inside the Capacitor iOS app. Deliver web previews from object storage behind a CDN.
- Run multiple stateless FastAPI instances behind a managed load balancer. Keep sessions and authorization state out of process memory.
- Use managed PostgreSQL with automated backups, point-in-time recovery, read replicas for read-heavy analytics, and PgBouncer or provider-side pooling.
- Move slow classification and report work to a managed job queue if it outgrows synchronous API requests.
- Add bank connections only through a regulated provider and explicit user consent. Store provider tokens in a managed secrets service.

## Before production traffic

- Replace development defaults with required deployment secrets. Fail startup if the signing key is missing or weak.
- Turn off table creation at API startup. Run reviewed Alembic migrations as a deployment step.
- Set an explicit HTTPS CORS allowlist for web origins. Native Capacitor requests need their app origin allowed as well.
- Move the optional OpenAI merchant classification call off the synchronous transaction request path before enabling it at scale.
- Add request and login rate limits, idempotency keys for transaction imports, audit trails for account and credential changes, and abuse controls.
- Add database indexes from observed query plans, per-request timeouts, bounded retry behavior, structured logs, traces, and service-level dashboards.
- Add a secret rotation procedure, encryption key management, deletion/export workflows, incident response, and financial-data retention rules.
- Complete threat modeling and a security review before storing bank credentials, full card data, or imported transaction messages.

## Scale is measured, not assumed

Start with load tests for login, transaction ingestion, dashboard summary, and report generation using realistic data distributions. Track API latency, database pool wait time, worker queue age, error rate, and cost per active user. Scale the component that is saturated; do not increase every service at once.

The client authenticates and reads and writes account-specific data. Users can enter purchases or paste supported Indian bank SMS alerts; the original SMS is discarded after parsing. There is no automatic SMS access, bank connection, subscription detection, benefits tracker, or payment routing. Review reward catalog values before relying on them for a financial decision.
