# AGENTS.md - Fintech Banking API

Guidelines for AI coding agents working on this Django REST Framework fintech banking API.

## Project Overview

- **Framework**: Django 6.0.3 + Django REST Framework 3.17.1
- **Python**: 3.12 | **Database**: PostgreSQL (SQLite for dev fallback)
- **Settings**: `config.settings.local` (dev), `config.settings.production` (prod)
- **Apps**: `core_apps/` | **Auth**: JWT (simplejwt) + Djoser + Argon2

## Build & Run Commands

```bash
pipenv install && pipenv shell  # Setup
python manage.py runserver      # Server
python manage.py makemigrations && python manage.py migrate  # Database
python manage.py createsuperuser
python manage.py test                           # ALL tests
python manage.py test core_apps.user_auth       # Single app
python manage.py test core_apps.user_auth.tests.UserAuthTestCase  # Test class
python manage.py test core_apps.user_auth.tests.UserAuthTestCase.test_user_registration  # Single test
python manage.py test -v 2                      # Verbose
coverage run --source='.' manage.py test && coverage report -m  # Coverage
celery -A config worker -l info && celery -A config beat -l info  # Celery
```

## Import Order (PEP 8)

```python
# 1. Standard library
import os
from pathlib import Path

# 2. Django
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

# 3. Third-party
from rest_framework import serializers, viewsets

# 4. Local apps
from core_apps.common.models import BaseModel
```

## Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Models | PascalCase singular | `UserProfile`, `Transaction` |
| Views/ViewSets | PascalCase + suffix | `UserViewSet`, `AccountAPIView` |
| Serializers | PascalCase + Serializer | `UserSerializer`, `AccountCreateSerializer` |
| URLs | lowercase, hyphens | `user-profile`, `bank-accounts` |
| Settings/Functions | SCREAMING_SNAKE_CASE / snake_case | `MAX_UPLOAD_SIZE`, `get_balance()` |

## App Structure

```
core_apps/app_name/
├── __init__.py | admin.py | apps.py | models.py | views.py | serializers.py | urls.py | tests.py
└── migrations/__init__.py
```

## Model Conventions

```python
from django.db import models
from django.utils.translation import gettext_lazy as _

class Account(models.Model):
    user = models.ForeignKey(
        "user_auth.User",
        on_delete=models.CASCADE,
        related_name="accounts",
        verbose_name=_("user"),
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("Account")
        verbose_name_plural = _("Accounts")
        ordering = ["-created_at"]
        default_auto_field = "django.db.models.BigAutoField"
```

- Use `gettext_lazy as _` for all user-facing strings
- Always set `related_name` on ForeignKey/ManyToMany fields
- Use string references for model references ("user_auth.User")

## ViewSet Patterns

```python
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "account_type"]
    search_fields = ["account_number"]
    ordering_fields = ["created_at", "balance"]
    
    def get_queryset(self):
        return self.request.user.accounts.all()
```

## Serializer Patterns

```python
from rest_framework import serializers

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name"]
    
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
```

## URL Patterns

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AccountViewSet

router = DefaultRouter()
router.register(r"accounts", AccountViewSet, basename="account")

urlpatterns = [path("", include(router.urls))]
```

## Error Handling & Logging

```python
from rest_framework.exceptions import ValidationError, NotFound
from loguru import logger

try:
    account = Account.objects.get(id=account_id)
except Account.DoesNotExist:
    logger.error(f"Account not found: {account_id}")
    raise NotFound(detail="Account not found")

# Log levels: debug, info, warning, error, critical
# Logs: logs/debug.log (DEBUG), logs/error.log (ERROR/CRITICAL)
```

## Security Best Practices (Fintech)

- Use Argon2 for password hashing (already configured)
- Always validate input with serializers
- Use `write_only=True` for sensitive fields (passwords, tokens)
- Use `IsAuthenticated` permission for protected endpoints
- Never log sensitive data (passwords, account numbers, balances)
- Use database transactions for financial operations

## Environment Variables

- Location: `.envs/.env.local` (gitignored) | Template: `.envs/.env.example`
- Access: `from os import getenv; SECRET_KEY = getenv("SECRET_KEY")`

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `djangorestframework` | REST API | `djoser` + `simplejwt` | Auth |
| `drf-spectacular` | OpenAPI docs | `django-filter` | API filtering |
| `celery` + `django-celery-beat` | Background tasks | `loguru` | Logging |
| `cloudinary` | Media storage | `django-countries` | Country fields |

## File Locations

- Settings: `config/settings/` | URLs: `config/urls.py`
- Apps: `core_apps/` | Requirements: `requirements/`
- Logs: `logs/` | Docker: `docker/local/django/`
