"""Test settings — minimal config for running tests without external services."""
from os import getenv
from dotenv import load_dotenv
from pathlib import Path

# Load the local env (if present) so our defaults can be overridden
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
local_env_file = BASE_DIR / ".envs" / ".env.local"
if local_env_file.exists():
    load_dotenv(local_env_file)

from config.settings.base import *  # noqa: F403
from config.settings.base import BASE_DIR, SIMPLE_JWT  # noqa: F401

# --- Override anything that needs real infrastructure ---

SECRET_KEY = getenv("SECRET_KEY") or "django-insecure-test-key-12345"
SIGNING_KEY = getenv("SIGNING_KEY") or SECRET_KEY
# Ensure SIMPLE_JWT picks up our SIGNING_KEY override
SIMPLE_JWT["SIGNING_KEY"] = SIGNING_KEY

DEBUG = True

# Use SQLite in-memory for tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Local settings that tests depend on
OTP_EXPIRATION = timedelta(minutes=5)  # noqa: F405
LOCKOUT_DURATION = timedelta(minutes=1)  # noqa: F405
LOGIN_ATTEMPTS = 3

# Disable password hashers for speed
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable Celery — make tasks run synchronously
CELERY_TASK_ALWAYS_EAGER = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

# Dummy values for external services
CLOUDINARY_CLOUD_NAME = "test"
CLOUDINARY_API_KEY = "test"
CLOUDINARY_API_SECRET = "test"
SITE_NAME = "testbank"
DOMAIN = "localhost:8000"
ADMIN_URL = "admin/"
DEFAULT_FROM_EMAIL = "noreply@testbank.local"
BANK_NAME = "TestBank"
COOKIE_SECURE = False

# Default field values expected by Profile model
from datetime import date  # noqa: E402
DEFAULT_BIRTH_DATE = date(1990, 1, 1)
DEFAULT_DATE = date(2020, 1, 1)
DEFAULT_EXPIRY_DATE = date(2030, 1, 1)
DEFAULT_COUNTRY = "US"
DEFAULT_PHONE_NUMBER = "+12025551234"

# Email backend for tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
