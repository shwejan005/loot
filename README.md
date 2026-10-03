# Loot Wallet

Loot helps people in India choose among their Apple Pay eligible cards before checkout. It includes a Chrome extension that identifies the current shopping site, a mobile-first wallet for saving card names, a FastAPI API, and a starter Indian card catalog.

## What works

- Account registration, sign-in, and session restore.
- Add and remove cards by catalog name; card numbers and security details are not requested.
- Use the Chrome extension to detect the active shopping site and instantly compare eligible Axis Bank cards.
- Add purchases manually or paste a supported bank SMS alert.
- Classify merchants, estimate card rewards, and compare the cards in your wallet before a purchase.
- View recent activity, monthly totals, spending categories, and card utilization.
- Install the responsive client as an iOS app with Capacitor.

For the full product, architecture, data model, API, reward logic, setup, and current limitations, see the [Loot Wallet project guide](docs/loot-wallet-project-guide.md).

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

## Chrome extension

The extension reads the active tab's URL and page title, then shows the best matching eligible card. It starts with a ₹1,000 example purchase and lets you change the amount for a closer reward estimate. It does not read checkout forms or control Apple Pay's payment sheet.

Follow [the extension setup guide](frontend/extension/README.md) to load it in Chrome for local development.

At the India launch on 30 September 2026, Apple lists eligible Axis Bank Visa and Mastercard credit cards. The supported bank list can change; check [Apple's current India support list](https://www.apple.com/in/apple-pay/banks/in/en-in.html).

## iOS

iOS build and signing require macOS with Xcode. Set `NEXT_PUBLIC_API_URL` to the reachable HTTPS API address, then run `npm run ios:add` once. For later web updates use `npm run ios:sync`, and open Xcode with `npm run ios:open`.

The current Capacitor app cannot launch Loot on the side-button double-click. In India, that gesture opens Apple Pay so the user can authenticate and pay; Loot provides the card suggestion before that step. Apple documents the side-button flow in its [India launch announcement](https://www.apple.com/in/newsroom/2026/09/apple-pay-launches-in-india/). A future iOS quick action should use a supported App Shortcut entry point such as the Action button, rather than compete with Apple Pay's payment gesture.

## Current scope

Loot Wallet does not connect to banks or card networks, select a card in Apple Pay, or authorize payments. Transactions are entered by the user or imported from pasted SMS alerts. The reward catalog is a starter dataset and reward estimates are indicative; issuer offers and eligibility rules can change. Subscription detection, automatic message access, and production account security workflows are not implemented. See [production scale notes](docs/production-scale.md) before handling real financial data.

## Repository layout

```text
backend/   FastAPI API, SQLAlchemy models, reward engine, seed data
frontend/  Next.js wallet, Chrome extension, and Capacitor iOS configuration
shared/    Shared-project notes
docs/      Architecture and production readiness notes
```
