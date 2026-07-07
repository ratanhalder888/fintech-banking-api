# AGENTS.md

## Architecture Reality
- Scaffold with auth wired and working. `core_apps/user_auth` has User model (custom, email-based), serializers, views, OTP login, account lockout.
- `core_apps/common` has `TimeStampedModel`, `ContentView` (generic FK), `CookieAuthentication`, custom renderers.
- `core_apps/user_profile` has profile model, serializers, signals, views.
- Auth endpoints wired at `/api/v1/auth/` — Djoser (`djoser.urls`) + custom routes in `core_apps/user_auth/urls.py` (login, verify-otp, refresh, logout).
- Schema at `/api/v1/schema/` via drf-spectacular (Swagger, ReDoc, OpenAPI JSON).
- No banking/business API routes exist yet. `config/settings/production.py` is empty.
- **Zero tests** in repo. `python manage.py test` finds nothing.

## Auth Flow (Non-obvious)
- Login is OTP-based: `POST /api/v1/auth/login/` sends OTP → `POST /api/v1/auth/verify-otp/` returns JWT + sets `access` cookie.
- Default DRF auth class is `CookieAuthentication` (`core_apps/common/cookie_auth.py`). Reads JWT from `access` cookie (fallback) or `Authorization` header (takes priority).
- JWT signing requires `SIGNING_KEY` env var.
- Login lockout: 3 failed attempts → account locked for 1 minute (`LOGIN_ATTEMPTS=3`, `LOCKOUT_DURATION=timedelta(minutes=1)` in `config/settings/local.py`).
- Custom user model: `AUTH_USER_MODEL="user_auth.User"`. `USERNAME_FIELD="email"`. BigInteger PK via `generate_user_id()`.

## Environment + Settings
- Env loaded from `.envs/.env.local` by both `base.py` and `local.py` (loaded twice — redundant but harmless).
- `.envs/*` gitignored except `.env.example`. Copy `.env.example` → `.env.local` to start.
- Required env vars: `SECRET_KEY`, `DEBUG`, `SITE_NAME`, `ADMIN_URL`, `DOMAIN`, `EMAIL_HOST`, `EMAIL_PORT`, `DEFAULT_FROM_EMAIL`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_DB`, `POSTGRES_PASSWORD`, `SIGNING_KEY`.
- `DEBUG` read as raw string from env — "True"/"False" (not boolean).
- PostgreSQL only. SQLite config in `base.py` is commented out.
- `local.py` hardcodes `EMAIL_HOST="mailpit"`, `EMAIL_PORT=1025` (overrides env values — mailpit for Docker dev, not real SMTP).
- `ADMIN_URL` is configurable — Django admin path not hardcoded. Set via env.
- `ALLOWED_HOSTS`: localhost, 127.0.0.1, 0.0.0.0. `CSRF_TRUSTED_ORIGINS`: `http://localhost:8080`, `http://127.0.0.1:8080`.
- `manage.py` defaults to `DJANGO_SETTINGS_MODULE=config.settings.local`.

## Dependencies
- Two dependency paths: `Pipfile`/`Pipfile.lock` AND `requirements/*.txt`. They are kept in sync.
- Install: `pip install -r requirements/local.txt` (includes base + watchfiles).
- Docker builds from `requirements/local.txt` via `pip wheel` multi-stage build (`BUILD_ENVIRONMENT=local`).
- Django 6.0.3 (not LTS), Python 3.12.

## Docker
- **Prerequisite**: `docker network create banker_local_nw` (external network in `local.yml`).
- App accessed via nginx at `http://localhost:8080`, NOT `:8000`. Port 8000 is internal-only in Docker.
- Services: api, postgres, redis, rabbitmq, mailpit, celeryworker, celerybeat, flower(:5555), nginx(:8080).
- Mailpit SMTP at localhost:1025, web UI at localhost:8025.
- Entrypoint waits for PostgreSQL, then `/start.sh` runs `migrate --no-input`, `collectstatic --no-input`, `runserver 0.0.0.0:8000`.
- Makefile targets: `make build` (build + up), `make up`, `make down`, `make makemigrations`, `make migrate`, `make superuser`, `make collectstatic`, `make flush`, `make banker-db` (psql), `make network-inspect`.

## Local Dev (No Docker)
- `python manage.py migrate` then `python manage.py runserver`. Server on port 8000.
- Requires running PostgreSQL + Redis (for Celery broker). RabbitMQ also needed if Celery workers run.

## Logging
- All logging routed through Loguru via `logging_utils.InterceptHandler` (captures stdlib logging).
- Console: INFO+ to stderr. `logs/debug.log`: DEBUG+ (10MB rotation, 30d retention). `logs/error.log`: ERROR+ (10MB rotation, 30d, with backtrace/diagnose).
- Loguru configured once at module level in `config/settings/base.py` — not in middleware/app config.

## Known Bugs/Gotchas
- `config/settings/base.py:276`: `api_secret = "CLOUDINARY_API_SECERET"` is a string literal, not reading from env var. Cloudinary uploads will fail without fix.
- `local.py` imports `timedelta` from `base.py` via wildcard import but uses it directly — fragile import order.
- Docker compose uses external network; if missing, `docker compose up` fails with unclear error.
