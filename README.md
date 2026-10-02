# Loot Wallet

Loot Wallet tracks credit card purchases, compares card rewards, and shows where spending and missed rewards are adding up. It includes a mobile-first Next.js client, a FastAPI API, and a seeded catalog of popular Indian credit cards.

## What works

- Account registration, sign-in, and session restore.
- Add and remove cards from the catalog; choose a default card and optionally save its last four digits.
- Add purchases manually or paste a supported bank SMS alert.
- Classify merchants, estimate card rewards, and compare the cards in your wallet before a purchase.
- View recent activity, monthly totals, spending categories, and card utilization.
- Install the responsive client as an iOS app with Capacitor.

Purchase records and user accounts persist in the configured database. The local default is SQLite; PostgreSQL can be configured with `DATABASE_URL`. Merchant classification uses local keyword rules and can use the OpenAI API when a key is configured.

## Quick start

Use Python 3.10+ and Node.js 22+.

Start the backend in one terminal:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

On first start, the API creates the local SQLite database and seeds the Indian card catalog. API documentation is at http://localhost:8000/docs.

Start the client in a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open http://localhost:3000, create an account, add a card, and record a purchase. The client uses `http://localhost:8000` by default. Set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` when the API runs elsewhere; rebuild the static bundle after changing it.

## iOS

iOS build and signing require macOS with Xcode. Set `NEXT_PUBLIC_API_URL` to the reachable HTTPS API address, then run `npm run ios:add` once. For later web updates use `npm run ios:sync`, and open Xcode with `npm run ios:open`.

## Current scope

Loot Wallet does not connect to banks or card networks. Transactions are entered by the user or imported from pasted SMS alerts. The reward catalog is a starter dataset and reward estimates are indicative; issuer offers and eligibility rules can change. Subscription detection, automatic message access, and production account security workflows are not implemented. See [production scale notes](docs/production-scale.md) before handling real financial data.

## Repository layout

```text
backend/   FastAPI API, SQLAlchemy models, reward engine, seed data
frontend/  Next.js client and Capacitor iOS configuration
shared/    Shared-project notes
docs/      Architecture and production readiness notes
```
