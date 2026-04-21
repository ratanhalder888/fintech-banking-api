# AGENTS.md

## Repo Reality (verify before coding)
- This is an early scaffold, not a finished banking API: most app files in `core_apps/*` are Django stubs.
- `config/urls.py` only routes Django admin (`path(f"{settings.ADMIN_URL}", admin.site.urls)`); no API routes are wired yet.
- `manage.py` defaults to `DJANGO_SETTINGS_MODULE=config.settings.local`.
- `config/settings/production.py` is currently empty.

## Environment + settings gotchas
- Settings load env vars from `.envs/.env.local` in both `config/settings/base.py` and `config/settings/local.py`.
- PostgreSQL is required by current settings (`django.db.backends.postgresql` in `config/settings/base.py`); there is no active SQLite fallback.
- Minimum env keys to run locally come from `.envs/.env.example`: `SECRET_KEY`, `DEBUG`, `ADMIN_URL`, mail vars, and `POSTGRES_*`.
- `DEBUG` is read from env as a string in `config/settings/local.py`; keep that in mind when debugging env issues.

## Dependency + run workflow
- Two dependency paths exist: `Pipfile`/`Pipfile.lock` and `requirements/*.txt`.
- Docker builds from `requirements/local.txt` via `docker/local/django/Dockerfile` (`BUILD_ENVIRONMENT=local`), not from Pipfile.
- Local Docker entrypoint waits for Postgres (`docker/local/django/entrypoint.sh`), then `/start.sh` runs `migrate`, `collectstatic`, and `runserver 0.0.0.0:8000`.

## High-value commands
- Local Python flow: `python manage.py migrate`, then `python manage.py runserver`.
- Tests: `python manage.py test` (currently very small test surface).
- Docker flow via `Makefile`: `make build` (build + up), `make up`, `make down`, `make makemigrations`, `make migrate`.

## Docker compose quirk
- `local.yml` uses external network `banker_local_nw`; create it first if missing:
  - `docker network create banker_local_nw`

## Logging
- Logging is routed through Loguru using `logging_utils.InterceptHandler`.
- File logs are expected at `logs/debug.log` and `logs/error.log` (directory is created in Docker image, not guaranteed outside Docker).
