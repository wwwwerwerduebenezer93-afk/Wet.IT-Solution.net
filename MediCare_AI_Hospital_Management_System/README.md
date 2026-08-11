# MediCare AI Hospital Management System

A responsive hospital dashboard and clinical decision-support prototype built with React, TypeScript and Vinext/Next-compatible components.

## Included features

- Patient registration with age, sex/gender, blood group, email, phone and password fields
- Six-digit email/SMS verification-code field (interface demonstration)
- Permission-based browser geolocation
- Permission-based live camera capture
- Permission-based voice-to-text symptom entry (supported browsers)
- Patient QR identifier and digital patient card
- One-click SMS, email, WhatsApp and telephone links using each patient's saved contact details
- Editable hospital message subject and template before opening the selected communication channel
- AI-assisted triage with demographic risk flags and emergency warning signs
- Patient search, appointments, clinical records, pharmacy and laboratory modules
- Responsive desktop, tablet and mobile layouts plus dark mode
- Clear clinical-safety and privacy messaging

## Run in Visual Studio Code

1. Install Node.js 22 or later from https://nodejs.org/.
2. Extract this ZIP and open the extracted folder in Visual Studio Code.
3. Open **Terminal → New Terminal**.
4. Run `npm install`.
5. Run `npm run dev`.
6. Open the local address shown in the terminal (normally `http://localhost:5173`).

For camera, voice and location, allow the browser permission only when you want to test that feature. These APIs work on localhost or an HTTPS-hosted site.

## Production and real hospital use

This package is a functional front-end prototype. The sample records are held in browser memory and reset when the page reloads. Before handling real patient information, connect it to a secure server and database, implement actual email/SMS delivery, use a vetted identity provider, encrypt data, add role-based permissions and audit logs, complete clinical validation, perform cybersecurity testing and obtain all required legal, privacy and health-authority approvals.

The triage feature is not a medical diagnosis and must not replace a licensed clinician. Ghana emergency services: **112**.

## Useful commands

- `npm run dev` — start development mode
- `npm run build` — create and validate the production build
- `npm run lint` — check code quality
- `npm test` — build and run the included rendering test
