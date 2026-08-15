# Production Hardening Checklist

Quick checklist and recommendations for deploying the Task Manager backend to production.

- Use HTTPS (TLS) via a reverse proxy (nginx) or a managed host (Heroku, Render, Fly.io).
- Replace in-process scheduler (`APScheduler`) with an external worker (Celery + Redis, Cloud Scheduler + Cloud Functions) for reliability.
- Store secrets securely (environment variables, Vault, or platform secrets manager). Do NOT commit `FCM_SERVER_KEY`.
- Enable secure cookie flags: `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE='Lax'`.
- Add rate-limiting (Flask-Limiter) to auth and API endpoints.
- Enable CORS only for known origins (use `Flask-Cors` carefully).
- Add logging, monitoring, and error reporting (Sentry or similar).
- Use a managed database or regular backups for SQLite (migrate to Postgres for concurrency).
- Add automated tests and CI pipeline (lint, unit tests, security checks).
