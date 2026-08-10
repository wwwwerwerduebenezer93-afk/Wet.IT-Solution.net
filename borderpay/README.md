# BorderPay cross-border payment prototype

BorderPay is a responsive demonstration app featuring account creation, hashed passwords and payment PINs, separate email and phone-code verification, live-camera photo capture, QR receiving details, country selection, PIN-gated transfers, transaction history and local AI-assisted help search. Payments are deliberately simulated.

## Run locally

1. Install Node.js 20 or newer.
2. Open this folder in VS Code and open **Terminal → New Terminal**.
3. Run `npm install`.
4. Set a strong signing secret: macOS/Linux: `export JWT_SECRET="a-long-random-secret"`; Windows PowerShell: `$env:JWT_SECRET="a-long-random-secret"`.
5. Run `npm start` and open `http://localhost:3000`.

During email and phone verification, the six-digit codes appear inside the app because this is a self-contained demo. Data is stored in `data/store.json` after first use. AI Smart Search uses a curated local payment guide, so it requires no API key. Replace `/api/ai-search` with an approved hosted model and retrieval layer if you need generative answers in production; never send PINs, passwords, identity photos or verification codes to a model.

## Production checklist

Do not accept real money with this prototype. A production service needs licensed payment/FX partners, jurisdiction-specific authorisation, KYC/KYB, sanctions/PEP and AML monitoring, fraud controls, transaction limits, audited ledger accounting, PCI DSS controls, encrypted object storage, liveness/biometric consent controls, an email provider, secure secrets management, database transactions, backups, webhook verification, independent security testing and legal/privacy review. Replace the demo code delivery and simulated transfer endpoint with approved providers. Never store card data yourself.
