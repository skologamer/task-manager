# Task Manager

A minimal Flask-based task management app with calendar import, a progress tracker, and customizable browser notifications.

[![CI](https://github.com/skologamer/task-maanger/actions/workflows/pytest.yml/badge.svg)](https://github.com/skologamer/task-maanger/actions/workflows/pytest.yml)

[![Codecov](https://codecov.io/gh/skologamer/task-maanger/branch/main/graph/badge.svg)](https://codecov.io/gh/skologamer/task-maanger)
## Overview

Task Manager helps users keep daily responsibilities organized with a calendar view, quick task creation, reminder settings, and a simple progress dashboard.
## Features

- Task CRUD with due dates and reminder settings
- Calendar view (FullCalendar) and progress chart (Chart.js)
- Import events from `.ics` files
- Browser notifications scheduled before due times (configurable per task)

## Quick start

1. Create and activate a Python virtualenv:

```bash
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python app.py
```

4. Open http://127.0.0.1:5000 in your browser.

Notes:
- Browser notifications require permission; grant when prompted.
- Calendar sync here supports `.ics` imports. For full Google Calendar sync, configure OAuth and modify the server to use Google Calendar APIs.

## Mobile / Installable (PWA & Native wrappers)

This app is now a Progressive Web App (PWA). You can install it directly from mobile browsers (Add to Home Screen) or wrap it into native Android/iOS apps using Capacitor.

PWA test:

1. Run the server (`python app.py`) and open the site on your phone browser.
2. Use the browser menu to "Add to Home screen" or install when prompted.

Package with Capacitor (Android/iOS):

1. From the project root, install Capacitor in a Node environment:

```bash
npm init -y
npm install @capacitor/core @capacitor/cli --save
npx cap init task-manager com.example.taskmanager --web-dir=.
```

2. Build the web assets (ensure `index.html`, `static/` are in the web dir), then add platforms:

```bash
npx cap add android
# On macOS only:
npx cap add ios
npx cap open android
```

Notes:
- iOS native builds require a Mac with Xcode.
- Use `npx cap copy` after web changes, then `npx cap open <platform>` to continue native packaging.

If you want, I can scaffold a `package.json` + Capacitor config here and prepare the Android wrapper next.

### Local packaging steps (I scaffolded helper files)

Files added: `package.json`, `capacitor.config.json`, `scripts/prepare-web.js`.

To prepare and package the app for Android/iOS (run from project root):

```bash
# install node deps

npm install

# prepare the `www` folder from Flask templates/static
npm run prepare-web

# initialize capacitor (only needed first time)
npm run cap:init

# add android platform
npm run cap:add-android

# copy web assets into native projects after changes
npm run cap:copy

# open Android Studio to build/sign and run
npm run cap:open-android
```

On macOS you can also run `npm run cap:add-ios` and `npm run cap:open-ios`.

I can continue and run these steps for you (scaffold native projects) if you want—note I cannot run `npm` or open platform-specific tools from here, but I can generate configs and guide each step.

### Configuring API endpoint and CORS

- If you package the app as native, update `static/config.js` (and `www/static/config.js`) to point `API_BASE_URL` at your hosted Flask API, for example:

```js
var API_BASE_URL = 'https://tasks.example.com/api';
```

- Ensure your Flask backend allows requests from the app origin. This project enables CORS by default in `app.py` (uses `Flask-Cors`).

- Note: packaged apps (Capacitor) run from `file://` origins; CORS and server TLS must be configured accordingly.

## User accounts & API tokens

You can create a local account via the web UI (`/register`) or `/login`. The server supports session-based auth for the web UI and token-based auth for APIs used by native apps.

- To obtain an API token after login, visit `/api/token` (GET) which returns JSON: `{ "token": "..." }`.
- For native apps, include the token in requests as an Authorization header: `Authorization: Bearer <token>`.

Tasks are scoped to users — when authenticated (session or token) task list, creation, update, delete and imports are performed for the current user. Unauthenticated requests operate on anonymous tasks.

### Server-side scheduled reminders & Push (optional)

This project includes a server-side reminder checker that can send push notifications via Firebase Cloud Messaging (FCM). It uses `APScheduler` to check for upcoming tasks and `FCM_SERVER_KEY` environment variable to authorize requests.

How to enable:

1. Set the environment variable `FCM_SERVER_KEY` to your Firebase legacy server key on the machine running the Flask app.

```bash
set FCM_SERVER_KEY=AAA...your_key_here
```

2. Register device tokens from your mobile app by POSTing to `/api/register_token` with JSON `{ "token": "<device-token>", "platform": "android" }`.

3. The server will check tasks every minute and send pushes when a task's reminder time is reached. The scheduler runs in-process (suitable for single-instance deployments). For production use, run a separate scheduler worker or use cloud scheduling with a push-sending service.

Notes:

### Capacitor Push integration (client)

To register device tokens from a Capacitor native app, install the Capacitor Push plugin on your project:

```bash
npm install @capacitor/push-notifications
npx cap sync
```

Then call `initPush()` on app startup. This repository includes `static/push_client.js` and `www/static/push_client.js` which provide a small helper that registers with the native push SDK and POSTs the token to `/api/register_token`.

Example (call after app boot):

```js
if(window.initPush) window.initPush();
```

On Android you must add Firebase to the native project and configure the `google-services.json`. For iOS configure APNs and proper entitlements.

## Run tests in Docker

If your local environment doesn't have Python available, run the test suite inside Docker:

Build the image:

```bash
docker build -t task-manager .
```

Run tests with the image:

```bash
docker run --rm task-manager
```

Or use docker-compose:

```bash
docker-compose run --rm tests
```

These commands install dependencies from `requirements.txt` and run `pytest -q` inside a clean container.
