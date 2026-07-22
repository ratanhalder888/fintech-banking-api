"""
Tests for the auth service layer.

These tests hit the database (SQLite in-memory) but mock external
calls (email sending).  This is exactly what the Django Styleguide
recommends for service-layer tests.
"""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from core_apps.user_auth.services import (
    AccountLockedError,
    InvalidCredentialsError,
    InvalidOTPError,
    OTPExpiredError,
    login_initiate,
    otp_verify,
)

User = get_user_model()


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def user_data():
    return {
        "email": "alice@example.com",
        "password": "s3cret!",
        "first_name": "Alice",
        "last_name": "Wonder",
        "id_no": 123456,
        "security_question": "maiden_name",
        "security_answer": "Smith",
    }


@pytest.fixture
def enabled_user(user_data):
    """Create a user that is active and not locked out.

    Note: ``username`` is omitted from ``user_data`` because the custom
    ``UserManager._create_user`` auto-generates it via ``generate_username()``
    and would conflict if we also passed it.
    """
    return User.objects.create_user(**user_data)


# ------------------------------------------------------------------
# login_initiate
# ------------------------------------------------------------------

@pytest.mark.django_db
class TestLoginInitiate:
    def test_successful_login_sends_otp(self, enabled_user):
        """Happy path: valid credentials → OTP sent, failed attempts reset."""
        with patch(
            "core_apps.user_auth.services.send_otp_email"
        ) as mock_send_otp:
            login_initiate(
                email="alice@example.com",
                password="s3cret!",
            )

        # OTP should have been sent — refresh to get the latest value
        enabled_user.refresh_from_db()
        mock_send_otp.assert_called_once_with("alice@example.com", enabled_user.otp)
        # Failed attempts should be reset
        assert enabled_user.failed_login_attempts == 0

    def test_invalid_credentials_raises_error(self, enabled_user):
        """Wrong password → InvalidCredentialsError, attempt counter increments."""
        with patch(
            "core_apps.user_auth.services.send_otp_email"
        ) as mock_send_otp:
            with pytest.raises(InvalidCredentialsError):
                login_initiate(
                    email="alice@example.com",
                    password="wrong-password",
                )

        mock_send_otp.assert_not_called()
        enabled_user.refresh_from_db()
        assert enabled_user.failed_login_attempts == 1

    def test_too_many_failed_attempts_locks_account(self, enabled_user):
        """Exceed LOGIN_ATTEMPTS → AccountLockedError."""
        # The first N-1 attempts raise InvalidCredentialsError
        max_attempts = settings.LOGIN_ATTEMPTS
        for _ in range(max_attempts - 1):
            with pytest.raises(InvalidCredentialsError):
                login_initiate(
                    email="alice@example.com",
                    password="wrong",
                )

        # The Nth attempt crosses the threshold → locked
        with pytest.raises(AccountLockedError):
            login_initiate(
                email="alice@example.com",
                password="wrong",
            )

        enabled_user.refresh_from_db()
        assert enabled_user.failed_login_attempts == max_attempts

    def test_locked_account_cannot_log_in_even_with_correct_password(
        self, enabled_user
    ):
        """Locked out user gets AccountLockedError even with correct password."""
        max_attempts = settings.LOGIN_ATTEMPTS
        # Trigger lockout: N-1 wrong attempts
        for _ in range(max_attempts - 1):
            with pytest.raises(InvalidCredentialsError):
                login_initiate(email="alice@example.com", password="wrong")

        # Nth wrong attempt locks
        with pytest.raises(AccountLockedError):
            login_initiate(email="alice@example.com", password="wrong")

        enabled_user.refresh_from_db()

        # Correct password should still be rejected
        with pytest.raises(AccountLockedError):
            login_initiate(email="alice@example.com", password="s3cret!")

    def test_nonexistent_user_raises_error(self):
        """Login for email that never existed → InvalidCredentialsError (no lockout)."""
        with pytest.raises(InvalidCredentialsError) as exc_info:
            login_initiate(
                email="nobody@example.com",
                password="irrelevant",
            )
        assert "not correct" in str(exc_info.value)


# ------------------------------------------------------------------
# otp_verify
# ------------------------------------------------------------------

@pytest.mark.django_db
class TestOTPVerify:
    def test_valid_otp_returns_tokens(self, enabled_user):
        """Happy path: correct, non-expired OTP → JWT tokens returned."""
        # Manually set an OTP (as login_initiate would)
        otp = "123456"
        enabled_user.set_otp(otp)

        result = otp_verify(otp=otp)

        assert result.user_id == enabled_user.id
        assert result.access_token is not None
        assert result.refresh_token is not None

        # OTP should be cleared after successful verification
        enabled_user.refresh_from_db()
        assert enabled_user.otp == ""

    def test_invalid_otp_raises_error(self, enabled_user):
        """OTP that doesn't match → InvalidOTPError."""
        enabled_user.set_otp("999999")

        with pytest.raises(InvalidOTPError):
            otp_verify(otp="000000")

    def test_expired_otp_raises_error(self, enabled_user):
        """OTP past its expiry → OTPExpiredError."""
        enabled_user.set_otp("123456")
        # Manually push expiry into the past
        enabled_user.otp_expiry_time = timezone.now() - timedelta(seconds=1)
        enabled_user.save(update_fields=["otp_expiry_time"])

        with pytest.raises(OTPExpiredError):
            otp_verify(otp="123456")

    def test_locked_user_cannot_verify_otp(self, enabled_user):
        """Locked out user → AccountLockedError even with valid OTP."""
        enabled_user.set_otp("123456")

        # Lock the account
        enabled_user.account_status = User.AccountStatus.LOCKED
        enabled_user.last_failed_login = timezone.now()
        enabled_user.save(update_fields=["account_status", "last_failed_login"])

        with pytest.raises(AccountLockedError):
            otp_verify(otp="123456")
