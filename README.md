# Banker

> The Django banking API scaffold that ships with OTP login, role-based users, JWT cookies, and zero-config Docker from day one.

---

## What It Does

Banker gives you a production-ready REST API foundation for banking applications — secure authentication, multi-role user management, Celery-powered background jobs, and OpenAPI docs — all wired and working before you write a single line of banking logic.

**Auth is not a feature you bolt on later.** Banker ships OTP-based login, JWT via HTTP-only cookies, account lockout after 3 failed attempts, and Argon2 password hashing out of the box.

---

## Motivation

Every fintech project I've seen starts the same way: spend two weeks wiring up Django REST Framework, SimpleJWT, Djoser, Celery, Docker Compose, Swagger docs, and Loguru logging — then another week debugging cookie auth and account lockout. That's 3 weeks before you write any code that matters.

Banker collapses that to zero. Clone → one `make build` command → hit `http://localhost:8080/api/v1/auth/login/` and you already have:

- OTP-based login with email delivery (Mailpit for dev)
- JWT stored in HTTP-only `access`/`refresh` cookies
- Account lockout after failed logins
- User roles (Customer, Teller, Account Executive, Branch Manager)
- Bank accounts with deposits and manager verification
- User profiles with next-of-kin and Cloudinary photo uploads
- Celery workers ready for async tasks
- Swagger + ReDoc at `/api/v1/schema/`

**Stop scaffolding. Start banking.**

---

## Quick Start

### With Docker (recommended)

```bash
# 1. Clone
git clone <repo-url> && cd fintech-banking-api

# 2. Create env file
cp .envs/.env.example .envs/.env.local
# Fill in SECRET_KEY, SIGNING_KEY, POSTGRES_* values

# 3. Create Docker network (once)
docker network create banker_local_nw

# 4. Build and start everything
make build
```

API is live at **http://localhost:8080**. Services running:

| Service | URL |
|---------|-----|
| API (via nginx) | `http://localhost:8080` |
| Swagger UI | `http://localhost:8080/api/v1/schema/swagger-ui/` |
| ReDoc | `http://localhost:8080/api/v1/schema/redoc/` |
| Mailpit (dev mail) | `http://localhost:8025` |
| Flower (Celery) | `http://localhost:5555` |
| RabbitMQ management | `http://localhost:15672` |

### Without Docker

```bash
git clone <repo-url> && cd fintech-banking-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/local.txt
cp .envs/.env.example .envs/.env.local
# Requires running PostgreSQL. Fill in POSTGRES_* values.

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver     # → http://localhost:8000
```

---

## Usage

### Authentication Flow

Banker uses OTP-based login, not password-for-token. Here's the full flow:

**1. Register a user**

```bash
curl -X POST http://localhost:8080/api/v1/auth/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@bank.com",
    "username": "alice",
    "password": "Str0ngP@ss!",
    "re_password": "Str0ngP@ss!",
    "first_name": "Alice",
    "last_name": "Smith",
    "id_no": 1001,
    "security_question": "maiden_name",
    "security_answer": "Johnson"
  }'
```

**2. Request OTP**

```bash
curl -X POST http://localhost:8080/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@bank.com", "password": "Str0ngP@ss!"}'
```

Response: `{"success": "OTP sent to your email", "email": "alice@bank.com"}`

**3. Verify OTP** (check Mailpit at `http://localhost:8025` for the code)

```bash
curl -X POST http://localhost:8080/api/v1/auth/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{"otp": "123456"}' \
  -c cookies.txt
```

Returns JWT tokens and sets `access`/`refresh` cookies. Subsequent requests carry the cookie automatically:

```bash
curl http://localhost:8080/api/v1/auth/users/me/ -b cookies.txt
```

**4. Refresh tokens**

```bash
curl -X POST http://localhost:8080/api/v1/auth/refresh/ -b cookies.txt -c cookies.txt
```

**5. Logout** (blacklists refresh token, deletes cookies)

```bash
curl -X POST http://localhost:8080/api/v1/auth/logout/ -b cookies.txt
```

### Auth Endpoint Reference

Prefix: `/api/v1/auth/`

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `users/` | POST | No | Register new user |
| `users/me/` | GET, PUT, PATCH | Cookie | Get/update current user |
| `users/activation/{uid}/{token}/` | POST | No | Activate account |
| `users/reset_password/` | POST | No | Request password reset |
| `jwt/create/` | POST | No | Djoser JWT create (available but login/verify-otp is the primary flow) |
| `login/` | POST | No | Validate credentials → send OTP |
| `verify-otp/` | POST | No | Verify OTP → get JWT in cookies |
| `refresh/` | POST | Cookie | Refresh access + refresh tokens |
| `logout/` | POST | Cookie | Blacklist refresh, clear cookies |

### Profile Endpoint Reference

Prefix: `/api/v1/profiles/`

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `all/` | GET | Cookie | List all profiles (staff) |
| `my-profile/` | GET, PUT, PATCH | Cookie | Get/update own profile (photo upload via Cloudinary) |
| `my-profile/next-of-kin/` | GET, POST | Cookie | List/add next-of-kin |
| `my-profile/next-of-kin/{uuid}/` | GET, PUT, PATCH, DELETE | Cookie | Manage a next-of-kin entry |

### Account Endpoint Reference

Prefix: `/api/v1/accounts/`

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `verify/{uuid}` | POST | Cookie (staff) | Verify a bank account |
| `deposit/` | POST | Cookie | Deposit funds into an account |

### Security Behavior

- **3 failed logins** → account locked for 1 minute, email sent
- **JWT** stored in HTTP-only `access` cookie (30 min TTL) + `refresh` cookie (1 day)
- **Auth header priority**: `Authorization: Bearer <token>` is checked first, then cookies fallback
- **Password hashing**: Argon2 (primary), with PBKDF2 and bcrypt fallbacks
- **API throttling**: 50 req/day anonymous, 100 req/day authenticated

### Docker Make Commands

```bash
make build              # Build images + start all services
make up                 # Start services (detached)
make down               # Stop services
make down-v             # Stop + delete volumes
make makemigrations     # Generate migrations
make migrate            # Apply migrations
make superuser          # Create Django superuser
make collectstatic      # Collect static files
make flush              # Wipe database
make banker-db          # Connect to Postgres via psql
make network-inspect    # Inspect Docker network
```

---

## Project Structure

```
.
├── config/                     # Django settings, Celery, WSGI/ASGI
│   └── settings/
│       ├── base.py             # Shared config (DB, DRF, JWT, Celery, Loguru)
│       ├── local.py            # Dev overrides (mailpit, lockout, CSRF)
│       ├── production.py       # Empty — fill for production
│       └── test.py             # Test settings (SQLite in-memory, Celery eager)
├── core_apps/
│   ├── common/                 # TimeStampedModel, ContentView, CookieAuthentication
│   ├── user_auth/              # Custom User model, OTP login, account lockout
│   ├── user_profile/           # Profile + NextOfKin, Cloudinary photo uploads
│   └── accounts/               # BankAccount, Transaction, deposit, verification
├── tests/                      # pytest suite (uses config/settings/test.py)
├── docker/                     # Dockerfiles, entrypoint, nginx config
├── requirements/               # base.txt, local.txt, production.txt
├── logs/                       # debug.log + error.log (Loguru, 10MB rotation)
├── local.yml                   # Docker Compose (12 services)
├── Makefile                    # CLI shortcuts
└── manage.py
```

---

## Testing

Tests live in `tests/` and run against `config/settings/test.py` (SQLite in-memory, no external services, Celery eager).

```bash
# pytest is not in requirements/ — install it first
pip install pytest pytest-django

pytest
```

`pytest.ini` sets `testpaths = tests` with `--nomigrations --reuse-db`.

---

## Environment Variables

Copy `.envs/.env.example` → `.envs/.env.local`. Minimum required:

```env
SECRET_KEY=<django-secret>
SIGNING_KEY=<jwt-signing-key>
DEBUG=True
SITE_NAME=Banker
ADMIN_URL=admin
DOMAIN=localhost:8000
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=banker_user
POSTGRES_DB=banker_db
POSTGRES_PASSWORD=<password>
EMAIL_HOST=localhost
EMAIL_PORT=1025
DEFAULT_FROM_EMAIL=noreply@banker.local
BANK_NAME=Banker
BANK_CODE=<bank-code>
CURRENCY_CODE_BDT=<bdt-currency>
CURRENCY_CODE_GBP=<gbp-currency>
CURRENCY_CODE_USD=<usd-currency>
CLOUDINARY_CLOUD_NAME=<cloud-name>
CLOUDINARY_API_KEY=<api-key>
CLOUDINARY_API_SECRET=<api-secret>
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

**Gotchas:**
- `DEBUG` is read as a string (`"True"` / `"False"`), not a boolean
- `SIGNING_KEY` is mandatory — JWT tokens fail without it
- `local.py` hardcodes `EMAIL_HOST="mailpit"` / `EMAIL_PORT=1025` for Docker dev
- `ADMIN_URL` is configurable — Django admin is not at the default `/admin/`

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Framework | Django 6.0.3 + DRF 3.17.1 |
| Auth | SimpleJWT, Djoser, custom OTP + cookies |
| Database | PostgreSQL (SQLite config commented out) |
| Task queue | Celery 5.6.3 + django-celery-beat |
| Media storage | Cloudinary 1.44.1 (profile photos) |
| Broker | RabbitMQ (Docker), Redis (result backend) |
| Docs | drf-spectacular (OpenAPI 3.0) |
| Logging | Loguru (console + rotating file) |
| Python | 3.12+ |

---

## Contributing

```bash
git clone <repo-url> && cd fintech-banking-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/local.txt
cp .envs/.env.example .envs/.env.local
python manage.py migrate
python manage.py runserver
```

1. Branch: `git checkout -b feature/your-feature`
2. Commit with [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `refactor:`
3. Add tests under `tests/` (`pip install pytest pytest-django`, run with `pytest`)
4. Open a PR to `main`

---

## Roadmap

- [x] Core banking operations — accounts, deposits, account verification (transfers/ledger pending)
- [ ] Payment processing integration
- [ ] Expand test coverage beyond `user_auth` (pytest + factory_boy)
- [ ] CI/CD pipeline
- [ ] Production settings + gunicorn deployment
- [ ] Webhook support
- [ ] Rate limiting per endpoint

---

## License

MIT
