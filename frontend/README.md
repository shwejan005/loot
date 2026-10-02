# Loot Wallet client

Mobile-first Next.js client packaged for iOS with Capacitor. It connects to the FastAPI backend for authentication, card management, transactions, routing recommendations, and analytics.

## Run locally

Start the backend first (see [backend setup](../backend/README.md)), then run:

```powershell
npm ci
npm run dev
```

Open http://localhost:3000. The local API URL defaults to `http://localhost:8000`. To use another API, create `.env.local` with:

```text
NEXT_PUBLIC_API_URL=https://your-api.example.com
```

The value is compiled into the client bundle. Rebuild after changing it. For iOS, use an HTTPS host reachable from the device; `localhost` on an iPhone points to the phone itself.

## Build for iOS

Building and signing require macOS with Xcode installed.

1. Set `NEXT_PUBLIC_API_URL` to the deployed HTTPS API URL.
2. Create the native project once with `npm run ios:add`.
3. After web changes run `npm run ios:sync`.
4. Open Xcode with `npm run ios:open` to test and sign.

## Fonts

League Spartan is bundled at build time. Lemon Milk is the preferred display face, with League Spartan as the fallback. Add a properly licensed Lemon Milk font under `public/fonts` and register it with `@font-face` once a license is in place.

## Current scope

The client shows account-specific data from the API. It supports manual purchase entry and pasted bank SMS alerts; it cannot read device messages or connect to a bank. Card reward information comes from the starter catalog and is an estimate. See the [production scale notes](../docs/production-scale.md) for the remaining deployment work.
