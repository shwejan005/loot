# Loot Wallet API

FastAPI service for authentication, card catalog and wallet management, purchase imports, reward routing, and spending analytics.

## Local setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

The development defaults use SQLite at `backend/loot.db`. On startup, the API creates tables and seeds the Indian card catalog. Browse the endpoints at http://localhost:8000/docs.

For macOS or Linux, activate the environment with `source .venv/bin/activate` and copy the environment file with `cp .env.example .env`.

## Configuration

| Variable | Purpose | Local default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite:///./loot.db` |
| `JWT_SECRET` | Secret used to sign access tokens | Development placeholder; replace for deployment |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `1440` |
| `CORS_ORIGINS` | Comma-separated browser and Capacitor origins | Local Next.js origins and `capacitor://localhost` |
| `OPENAI_API_KEY` | Optional merchant classification service | Empty; keyword classification remains available |
| `OPENAI_MODEL` | OpenAI model used for classification | `gpt-4o-mini` |
| `CREATE_TABLES_ON_STARTUP` | Create schema at API startup | `true` |

To use PostgreSQL, set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL and install the included `psycopg2-binary` dependency. Set `CREATE_TABLES_ON_STARTUP=false` when schema changes are managed with Alembic.

## API areas

- `/auth`: register, login, current user.
- `/catalog`: issuers, card products, reward categories.
- `/cards`: add, list, update, and remove wallet cards.
- `/transactions`: add, import from pasted SMS, list, and view transactions.
- `/route`: compare the wallet's cards for a merchant and purchase amount.
- `/analytics`: monthly report, spending categories, and card utilization.

Every route except `/health`, `/auth/register`, `/auth/login`, and `/catalog` requires a bearer token. The client handles authentication and adds it to protected requests.

## Tests

Install the development dependencies and run the API integration tests from the `backend` directory:

```powershell
pip install -r requirements-dev.txt
python -m pytest
```

The tests use an isolated in-memory SQLite database and exercise authentication, catalog and wallet flows, reward routing, purchase imports, and analytics.

## Data and deployment

The local SQLite database and `.env` file are development conveniences. Configure a managed database, strong rotated secrets, HTTPS CORS origins, migrations, backups, rate limits, and account data export/deletion before deployment. The SMS importer parses an alert but does not store the original message.
