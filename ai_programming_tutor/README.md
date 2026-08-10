# UCC CodeMentor AI

Complete web prototype for **Development of an AI-Based Programming Tutor for an Introductory Computer Science Course**.

## Features

- Student registration, hashed passwords, lecturer/student roles
- Five Python concepts with seeded exercises
- Browser code editor and restricted Python execution
- Objective tests separated from AI explanations
- Three-level progressive hints with optional AI API
- Completion, attempt and hint tracking
- Lecturer dashboard and responsive interface
- Dedicated student, teacher and staff login portals
- Student course registration and staff operational dashboard
- Public link directory with downloadable QR codes for every major portal
- Email and phone verification with expiring hashed one-time codes
- Mandatory live-camera picture capture and a prompted verification pose
- Strong password policy and unique verified contact details
- Separate uploaded profile/ID picture and live camera picture
- Automatic browser location capture with staff-only Google Maps review
- SQLite quick start, MySQL support, Docker and automated tests

## Quick start

1. Install Python 3.11+.
2. In this folder run `python -m venv .venv`.
3. Activate it: Windows `.venv\Scripts\activate`; Linux/macOS `source .venv/bin/activate`.
4. Run `pip install -r requirements.txt`.
5. Copy `.env.example` to `.env` and change `SECRET_KEY`.
6. Run `python app.py`.
7. Open `http://127.0.0.1:5000`.

The SQLite database and sample users are created automatically.

## Demo accounts

- Student: `student@tutor.local` / `Student123!`
- Lecturer: `lecturer@tutor.local` / `Lecturer123!`
- Teacher portal: `teacher@tutor.local` / `Teacher123!`
- Staff portal: `staff@tutor.local` / `Staff123!`

Change these before any real deployment.

Demo accounts are pre-verified. New accounts must complete email, phone and camera-picture verification.

## MySQL

Create the database with `sql/mysql_schema.sql`, then set `DATABASE_URL=mysql+pymysql://USERNAME:PASSWORD@HOST/ai_programming_tutor` and run `flask --app app init-db`. Alternatively run `docker compose up --build`.

## Optional AI service

The local pedagogical engine works without a paid API. For an OpenAI-compatible chat-completions service, set `AI_API_URL`, `AI_API_KEY`, and `AI_MODEL`. Never commit real keys.

## Testing

Run `pytest -q`.

## Technical report

The package includes `AI_Programming_Tutor_Technical_Report.docx`, which documents the implemented architecture, modules, database, routes, code runner, tutoring logic, security controls, verification results, deployment, maintenance and production roadmap.

## Portal links and QR codes

- `/student/login` — student login
- `/teacher/login` — teacher login
- `/staff/login` — staff login
- `/course-registration` — student course registration
- `/links` — complete link and QR-code directory

Set `PUBLIC_BASE_URL` in `.env` to the deployed HTTPS address and restart the application. All QR PNG files are regenerated under `static/qr/` using that address.

## Email, phone and live-picture verification

New student registration requires a unique email address, unique phone number, strong password, uploaded profile/ID picture, current camera capture and browser geolocation. Six-digit codes are stored as hashes and expire after 10 minutes.

For demonstration, `VERIFICATION_MODE=development` displays both codes on the verification page. For deployment, configure SMTP settings and the SMS webhook settings in `.env`, then set `VERIFICATION_MODE=production`. Camera access requires HTTPS or localhost. Captured pictures are placed under the private application instance directory, which is excluded from the ZIP and source control.

Uploaded and camera pictures are stored privately. Location is stored as latitude, longitude, accuracy and capture time; authorized staff can open it in Google Maps. Camera and geolocation access require HTTPS or localhost and explicit browser permission.

The camera capture supports identity review but is not automated biometric liveness detection. A production identity-verification provider is required if automated liveness or face matching is needed.

If upgrading an existing database created by an earlier package version, back it up and apply a schema migration for the new verification, picture and location columns. For a fresh demonstration, start with a new database and the application will create the full schema automatically.

## Important security and research notes

The included process restriction is suitable for a supervised prototype. A public production service must run untrusted code in separate locked-down containers or micro-VMs with no network and strict CPU/memory limits. Obtain UCC approval before collecting student data, and never use AI responses as the sole basis for grading.
