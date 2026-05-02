# Fintech Banking API

A modern, scalable REST API foundation for building fintech and banking applications. Built with Django REST Framework and PostgreSQL, this project provides a production-ready scaffold with secure authentication, background job processing, and comprehensive API documentation.

> **Note:** This is an early-stage scaffold designed for rapid development. Core authentication is wired; API routes and business logic are ready for implementation.

---

## Why Fintech Banking API?

Building a banking API from scratch is complex. Authentication, logging, Docker setup, and deployment infrastructure are non-trivial challenges. This project solves this by providing:

- **Security-first architecture** with JWT authentication and Argon2 password hashing
- **Production-ready infrastructure** – Django settings for local/production, Docker Compose, and logging via Loguru
- **Developer experience** – Auto-generated API docs (Swagger/ReDoc), CLI commands, and Makefile shortcuts
- **Async processing** – Celery integration for background tasks like email and notifications
- **Cloud-ready** – Support for Cloudinary, AWS S3, and Sentry out of the box

No more starting from scratch. Focus on **what makes your fintech platform unique**, not infrastructure.

---

## Key Features

| Feature | Details |
|---------|---------|
| **JWT Authentication** | Secure token-based auth with access & refresh tokens |
| **User Management** | Registration, login, password reset via Djoser |
| **Social Auth** | OAuth integration ready |
| **Async Tasks** | Celery + Celery Beat for background jobs |
| **API Docs** | Auto-generated Swagger/ReDoc with drf-spectacular |
| **Advanced Logging** | Structured logging via Loguru (console + file) |
| **Cloud Storage** | Cloudinary & AWS S3 integration |
| **Monitoring** | Sentry & Prometheus metrics ready |
| **Phone Validation** | International phone number support |
| **Docker & Compose** | Local dev + production-ready setup |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Framework** | Django 6.0.3, Django REST Framework 3.17.1 |
| **Language** | Python 3.12+ |
| **Database** | PostgreSQL 14+ (primary), SQLite (development) |
| **Authentication** | JWT (SimpleJWT), Djoser, OAuth |
| **Task Queue** | Celery 5.6.3 + django-celery-beat |
| **API Docs** | drf-spectacular (OpenAPI 3.0) |
| **Async** | Celery with Redis broker |
| **Logging** | Loguru |
| **Containerization** | Docker & Docker Compose |

---

## Project Structure

```
fintech-banking-api/
├── config/                     # Django project settings & WSGI/ASGI
│   ├── settings/
│   │   ├── base.py            # Shared configuration
│   │   ├── local.py           # Development
│   │   └── production.py      # Production (empty, ready to fill)
│   ├── urls.py                # Root URL config (admin only currently)
│   ├── celery_app.py          # Celery configuration
│   ├── wsgi.py & asgi.py
│
├── core_apps/                  # Django applications (stubs ready for development)
│   ├── common/                # Shared utilities, base models
│   ├── user_auth/             # Authentication & user registration
│   └── user_profile/          # User profile management
│
├── docker/                     # Docker configuration
│   └── local/django/
│       ├── Dockerfile
│       └── entrypoint.sh
│
├── requirements/               # Python dependencies
│   ├── base.txt               # Shared
│   ├── local.txt              # Development
│   └── production.txt         # Production
│
├── local.yml                   # Docker Compose configuration
├── Makefile                    # Convenient CLI commands
├── Pipfile & Pipfile.lock     # Pipenv dependencies
├── manage.py                   # Django management script
└── logs/                       # Application logs (debug.log, error.log)
```

---

## Quick Start

### 1. Clone & Set Up

```bash
# Clone the repository
git clone <repository-url>
cd fintech-banking-api

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements/local.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .envs/.env.example .envs/.env.local

# Edit .envs/.env.local with your local settings
```

**Minimum required variables:**
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
SITE_NAME=Fintech Banking API
ADMIN_URL=admin
DOMAIN=localhost:8000
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
DEFAULT_FROM_EMAIL=noreply@fintech-banking-api.local
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=fintech_banking_api_user
POSTGRES_DB=fintech_banking_api_db
POSTGRES_PASSWORD=your_password
BANK_NAME=Your Bank Name
```

### 3. Set Up Database & Run

```bash
# Run migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

**API available at:** `http://localhost:8000`

---

## Using Docker

```bash
# Create Docker network (required once)
docker network create banker_local_nw

# Build and start services
make build

# Or use Docker directly
docker-compose -f local.yml up --build
```

Services run on: `http://localhost:8000`

---

## API Documentation

Once running, access documentation at:

- **Swagger UI:** `http://localhost:8000/api/schema/swagger-ui/`
- **ReDoc:** `http://localhost:8000/api/schema/redoc/`
- **OpenAPI Schema:** `http://localhost:8000/api/schema/`

### Authentication Endpoints (Djoser)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/users/` | POST | Register new user |
| `/auth/users/me/` | GET | Get current user |
| `/auth/jwt/create/` | POST | Obtain JWT token |
| `/auth/jwt/refresh/` | POST | Refresh token |
| `/auth/jwt/verify/` | POST | Verify token |
| `/auth/users/reset_password/` | POST | Reset password |
| `/auth/users/activation/` | POST | Activate account |

---

## Development

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test core_apps.user_auth
python manage.py test core_apps.user_profile

# Run with coverage report
coverage run --source='.' manage.py test
coverage report -m
```

### Useful Make Commands

```bash
make build              # Build Docker images
make up                 # Start services
make down               # Stop services
make makemigrations     # Create database migrations
make migrate            # Apply migrations
make shell              # Django shell
```

### Logging

Logs are managed by **Loguru** with three outputs:

- **Console:** INFO level and above
- **logs/debug.log:** DEBUG level (rotates at 10MB, 30-day retention)
- **logs/error.log:** ERROR & CRITICAL with full backtrace

---

## Production Deployment

### Environment Setup

1. Create `.envs/.env.production` with production settings
2. Set `DEBUG=False`
3. Install production dependencies:

```bash
pip install -r requirements/production.txt
```

### Production Dependencies

- **Gunicorn** – WSGI server
- **Uvicorn** – ASGI server (async support)
- **Sentry SDK** – Error tracking
- **django-prometheus** – Metrics
- **django-redis** – Caching layer
- **boto3 + django-storages** – AWS S3
- **django-health-check** – Health check endpoints

### Deployment Checklist

- [ ] Configure production database & Redis
- [ ] Set up Sentry for error tracking
- [ ] Configure email backend (SendGrid, AWS SES, etc.)
- [ ] Set up SSL/TLS certificates
- [ ] Configure CORS & ALLOWED_HOSTS
- [ ] Enable static file serving (WhiteNoise/CDN)
- [ ] Set up monitoring & alerting
- [ ] Run security checks (`python manage.py check --deploy`)
- [ ] Create comprehensive test suite
- [ ] Document API endpoints & workflows

---

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key | Yes |
| `DEBUG` | Debug mode (True/False) | Yes |
| `SITE_NAME` | Application name | Yes |
| `ADMIN_URL` | Admin panel URL path | Yes |
| `DOMAIN` | Application domain | Yes |
| `EMAIL_HOST` | SMTP server | Yes |
| `EMAIL_PORT` | SMTP port (usually 587) | Yes |
| `DEFAULT_FROM_EMAIL` | Sender email address | Yes |
| `POSTGRES_HOST` | Database host | Yes |
| `POSTGRES_PORT` | Database port (5432) | Yes |
| `POSTGRES_USER` | Database user | Yes |
| `POSTGRES_DB` | Database name | Yes |
| `POSTGRES_PASSWORD` | Database password | Yes |
| `BANK_NAME` | Financial institution name | No |

---

## Contributing

### Setting Up for Development

```bash
# Clone repository
git clone <repository-url>
cd fintech-banking-api

# Create & activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -r requirements/local.txt

# Copy environment template
cp .envs/.env.example .envs/.env.local

# Run migrations & start developing
python manage.py migrate
python manage.py runserver
```

### Submitting Changes

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes and write tests
3. Run the test suite: `python manage.py test`
4. Commit with clear messages: `git commit -m "feat: add your feature"`
5. Push to your fork: `git push origin feature/your-feature`
6. Open a Pull Request to `main`

### Code Style

- Follow [PEP 8](https://pep8.org/)
- Use meaningful variable names
- Add docstrings to functions and classes
- Keep functions small and focused

---

## Important Notes

### Current State

- **Early scaffold:** Core apps (`user_auth`, `user_profile`, `common`) are Django stubs ready for implementation
- **Admin only:** `config/urls.py` currently routes only Django admin; API routes need to be wired
- **PostgreSQL required:** Settings require PostgreSQL (no active SQLite fallback)
- **Production settings:** `config/settings/production.py` is empty and ready for configuration

### Known Requirements

- **PostgreSQL:** Must have a running PostgreSQL instance
- **Redis:** Needed for Celery broker (if using background tasks)
- **Docker network:** External network `banker_local_nw` must be created for Docker setup

### Environment Variable Gotchas

- `DEBUG` is read as a **string** from env in `local.py` – handle accordingly
- Environment files load from `.envs/.env.local` (not `.env`)
- Docker entrypoint waits for PostgreSQL before starting the app

---

## Roadmap

- [ ] Implement core banking operations (accounts, transactions)
- [ ] Add payment processing integration
- [ ] Create comprehensive test suite
- [ ] Set up CI/CD pipeline
- [ ] Implement rate limiting & throttling
- [ ] Add webhook support for external integrations
- [ ] Complete production settings configuration
- [ ] Document API thoroughly

---

## Support & Issues

For questions, bug reports, or feature requests:

1. Check existing [GitHub Issues](https://github.com/your-repo/issues)
2. Read [AGENTS.md](./AGENTS.md) for development guidelines
3. Open a new issue with clear details

---

## License

This project is licensed under the **MIT License** – see [LICENSE](LICENSE) for details.

---

**Made with ❤️ for fintech builders**
