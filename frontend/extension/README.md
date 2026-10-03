# Loot for Apple Pay

Loot for Apple Pay is a Chrome Manifest V3 extension. Click it on a shopping site and it reads that tab's URL and title to identify the merchant, then asks the Loot API to rank the Apple Pay eligible cards saved to your account. You can change the example purchase amount; the default is ₹1,000.

The extension sends the merchant name, amount, and Apple Pay India context to Loot. It does not read checkout fields or card details from the page. It only compares eligible Axis Bank Visa and Mastercard credit cards and shows an estimate from Loot's saved reward catalog.

## Run locally

1. Start the FastAPI service at `http://localhost:8000` and the Loot wallet at `http://localhost:3000`.
2. Create an account in the Loot wallet and add the name of each eligible card from the catalog.
3. In Chrome, open `chrome://extensions` and turn on **Developer mode**.
4. Choose **Load unpacked** and select this `frontend/extension` folder.
5. Open a shopping site, click the Loot extension, and sign in with your Loot username/email and password.

The extension stores only the Loot session token in Chrome extension storage. It does not store card numbers, expiry dates, or security codes.

## Deploying the API

Before distributing the extension, update `API_BASE` in `popup.js` to the HTTPS API origin and update `host_permissions` in `manifest.json` to match that origin. Then package and publish the extension through the Chrome Web Store. Never distribute a build that points at a development server.

## Current limits

- The recommendation is a pre-checkout suggestion. Loot cannot select a card inside Apple Pay or approve a payment.
- A ₹1,000 sample is used when the popup opens. Change it for an estimate closer to the intended purchase; the extension does not inspect checkout amounts.
- The merchant is inferred from the active tab's hostname and page title. An unfamiliar or payment-provider domain may be classified as `Other`.
- Apple Pay reward figures use Loot's local catalog and are estimates, not issuer-verified offers.
