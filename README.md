# Fintech-Banking API

A robust, scalable RESTful API for fintech and banking applications built with Django REST Framework. This API provides secure authentication, user management, and is designed to handle financial transactions and banking operations.

## Tech Stack

| Category | Technologies |
|----------|-------------|
| **Framework** | Django 6.0.3, Django REST Framework 3.17.1 |
| **Language** | Python 3.12 |
| **Database** | PostgreSQL (primary), SQLite (development) |
| **Authentication** | JWT (SimpleJWT), Djoser, Social Auth (OAuth) |
| **Task Queue** | Celery 5.6.3, django-celery-beat |
| **API Docs** | drf-spectacular (OpenAPI/Swagger) |
| **Storage** | Cloudinary (media), AWS S3 (production) |
| **Monitoring** | Sentry, django-prometheus |
| **Logging** | Loguru |

## Project Structure

```
fintech-banking-api/
├── config/                     # Django project configuration
│   ├── settings/
│   │   ├── base.py            # Shared settings
│   │   ├── local.py           # Development settings
│   │   └── production.py      # Production settings
│   ├── urls.py                # Root URL configuration
│   ├── asgi.py                # ASGI application
│   └── wsgi.py                # WSGI application
├── core_apps/                  # Application modules
│   ├── common/                # Shared utilities and base models
│   ├── user_auth/             # User authentication
│   └── user_profile/          # User profile management
├── docker/                     # Docker configuration
│   └── local/django/
│       ├── Dockerfile
│       └── entrypoint.sh
├── logs/                       # Application logs
│   ├── debug.log
│   └── error.log
├── requirements/               # Dependencies
│   ├── base.txt               # Shared dependencies
│   ├── local.txt              # Development dependencies
│   └── production.txt         # Production dependencies
├── .envs/                      # Environment files
│   ├── .env.example           # Environment template
│   └── .env.local             # Local environment (gitignored)
├── manage.py
├── Pipfile
└── Pipfile.lock
```

## Features

- **JWT Authentication** - Secure token-based authentication with access and refresh tokens
- **User Management** - Registration, login, password reset, email activation via Djoser
- **Social Authentication** - OAuth integration for multiple providers
- **Password Security** - Argon2 password hashing (industry-leading security)
- **API Documentation** - Auto-generated OpenAPI/Swagger docs
- **Background Tasks** - Celery integration for async processing
- **Advanced Logging** - Structured logging with Loguru
- **Cloud Storage** - Cloudinary integration for media files
- **Phone Number Validation** - International phone number support
- **Country Field Support** - Built-in country handling

## Prerequisites

- Python 3.12+
- PostgreSQL 14+
- Redis (for Celery broker)
- Pipenv or pip

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd fintech-banking-api
```

### 2. Set Up Virtual Environment

**Using Pipenv (Recommended):**

```bash
pipenv install
pipenv shell OR source .venv/bin/activates
```
s
**Using pip:**

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

pip install -r requirements/local.txt
```

### 3. Configure Environment Variables

```bash
cp .envs/.env.example .envs/.env.local
```

Edit `.envs/.env.local` with your configuration:

```bash
# Django Settings
SECRET_KEY="your-super-secret-key"
DEBUG="True"
SITE_NAME="Fintech Banking"
ADMIN_URL="admin"
DOMAIN="localhost:8000"

# Email Configuration
EMAIL_PORT="587"
EMAIL_HOST="smtp.example.com"
DEFAULT_FROM_EMAIL="noreply@example.com"

# PostgreSQL Database
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"
POSTGRES_USER="your_db_user"
POSTGRES_DB="fintech_banking_db"
POSTGRES_PASSWORD="your_db_password"

# Application Specific
BANK_NAME="Your Bank Name"
```

### 4. Set Up Database

```bash
# Create PostgreSQL database
createdb fintech_banking_db

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 5. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## Docker Setup

Build and run using Docker:

```bash
# Build the image
docker build -f docker/local/django/Dockerfile -t fintech-api .

# Run the container
docker run -p 8000:8000 --env-file .envs/.env.local fintech-api
```

## API Documentation

Once the server is running, access the API documentation at:

- **Swagger UI**: `http://localhost:8000/api/schema/swagger-ui/`
- **ReDoc**: `http://localhost:8000/api/schema/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

## Authentication Endpoints (via Djoser)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/users/` | POST | Register new user |
| `/auth/users/me/` | GET | Get current user |
| `/auth/jwt/create/` | POST | Obtain JWT token |
| `/auth/jwt/refresh/` | POST | Refresh JWT token |
| `/auth/jwt/verify/` | POST | Verify JWT token |
| `/auth/users/reset_password/` | POST | Request password reset |
| `/auth/users/activation/` | POST | Activate user account |

## Running Tests

```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test core_apps.user_auth
python manage.py test core_apps.user_profile
python manage.py test core_apps.common

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report -m
```

## Logging

The application uses Loguru for advanced logging:

- **Console**: INFO level and above
- **debug.log**: DEBUG level (rotates at 10MB, 30-day retention)
- **error.log**: ERROR and CRITICAL with full backtrace

Log files are stored in the `logs/` directory.

## Production Deployment

### Additional Production Dependencies

```bash
pip install -r requirements/production.txt
```

This includes:
- **Gunicorn** - WSGI server
- **Uvicorn** - ASGI server
- **Sentry SDK** - Error tracking
- **django-prometheus** - Monitoring
- **django-redis** - Caching
- **boto3 + django-storages** - AWS S3 storage
- **django-health-check** - Health endpoints

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure production database
- [ ] Set up Redis for caching and Celery
- [ ] Configure Sentry for error tracking
- [ ] Set up SSL/TLS certificates
- [ ] Configure CORS settings
- [ ] Set up static file serving (WhiteNoise/CDN)
- [ ] Configure email backend

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key | Yes |
| `DEBUG` | Debug mode (True/False) | Yes |
| `SITE_NAME` | Application name | Yes |
| `ADMIN_URL` | Admin panel URL path | Yes |
| `DOMAIN` | Site domain | Yes |
| `EMAIL_PORT` | SMTP port | Yes |
| `EMAIL_HOST` | SMTP host | Yes |
| `DEFAULT_FROM_EMAIL` | Default sender email | Yes |
| `POSTGRES_HOST` | Database host | Yes |
| `POSTGRES_PORT` | Database port | Yes |
| `POSTGRES_USER` | Database user | Yes |
| `POSTGRES_DB` | Database name | Yes |
| `POSTGRES_PASSWORD` | Database password | Yes |
| `BANK_NAME` | Bank/fintech name | No |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue in the GitHub repository.
