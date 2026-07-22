"""
Service layer for authentication business logic.

All business logic for the OTP login flow lives here.
Views should only call these services and handle HTTP concerns
(request parsing, response formatting, cookie setting).
"""
from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from loguru import logger
from rest_framework_simplejwt.tokens import RefreshToken

from core_apps.user_auth.emails import send_otp_email
from core_apps.user_auth.models import User
from core_apps.user_auth.utils import generate_otp


# ------------------------------------------------------------------
# Domain exceptions
# ------------------------------------------------------------------

class LoginError(Exception):
    """Base exception for login-flow errors."""


class InvalidCredentialsError(LoginError):
    """Email/password combination is wrong."""


class AccountLockedError(LoginError):
    """Account is temporarily locked due to too many failed attempts."""


class InvalidOTPError(LoginError):
    """OTP code does not match what was sent."""


class OTPExpiredError(LoginError):
    """OTP code was valid but has expired."""


# ------------------------------------------------------------------
# Service result types
# ------------------------------------------------------------------

@dataclass
class LoginInitiateResult:
    email: str


@dataclass
class OTPVerifyResult:
    access_token: str
    refresh_token: str
    user_id: int


# ------------------------------------------------------------------
# Services
# ------------------------------------------------------------------

def login_initiate(*, email: str, password: str) -> LoginInitiateResult:
    """
    Authenticate a user's credentials and initiate OTP-based login.

    1. Verify email + password via Django's authentication backend.
    2. If credentials are wrong, record the failed attempt and possibly
       lock the account (threshold = ``LOGIN_ATTEMPTS``).
    3. If credentials are correct, check whether the account is currently
       locked out (auto-unlock if the lockout period has elapsed).
    4. Reset failed-attempt counter, generate an OTP, persist it, and
       dispatch it by email.

    Returns
        ``LoginInitiateResult`` with the user's email.

    Raises
        ``InvalidCredentialsError`` -- email/password don't match.
        ``AccountLockedError`` -- account locked and still within lockout
        window.
    """
    user = authenticate(email=email, password=password)

    if user is None:
        # Credentials don't match — record the failed attempt
        existing_user = User.objects.filter(email=email).first()
        if existing_user:
            existing_user.handle_failed_login_attempts()
            if existing_user.failed_login_attempts >= settings.LOGIN_ATTEMPTS:
                logger.warning(
                    "Account locked due to failed attempts: %s", email
                )
                raise AccountLockedError(
                    f"You have exceeded the maximum number of login "
                    f"attempts. Your account has been locked for "
                    f"{settings.LOCKOUT_DURATION.total_seconds() / 60} "
                    f"minutes. An email has been sent to you with "
                    f"further instructions.",
                )
        else:
            logger.error("Failed login attempt for non-existent user: %s", email)

        raise InvalidCredentialsError("Your Login Credentials are not correct")

    # Check lockout (auto-unlocks if lockout period has elapsed)
    if user.is_locked_out:
        raise AccountLockedError(
            f"Account is locked due to multiple failed login attempts. "
            f"Please try again after "
            f"{settings.LOCKOUT_DURATION.total_seconds() / 60} minutes.",
        )

    # All checks passed — reset counters and send OTP
    user.reset_failed_login_attempts()

    otp = generate_otp()
    user.set_otp(otp)
    send_otp_email(user.email, otp)

    logger.info("OTP sent for login to user: %s", user.email)

    return LoginInitiateResult(email=user.email)


def otp_verify(*, otp: str) -> OTPVerifyResult:
    """
    Verify an OTP code and issue JWT tokens.

    1. Look up a user whose stored OTP matches and hasn't expired.
    2. If no match is found, distinguish between an expired OTP and
       an outright invalid one.
    3. Check account lockout status.
    4. Clear the OTP on the user record.
    5. Generate access + refresh JWTs.

    Returns
        ``OTPVerifyResult`` with tokens and user id.

    Raises
        ``InvalidOTPError`` -- the OTP code doesn't match.
        ``OTPExpiredError`` -- the OTP code was valid but has expired.
        ``AccountLockedError`` -- account locked and still within the
        lockout window.
    """
    user = User.objects.filter(
        otp=otp,
        otp_expiry_time__gt=timezone.now(),
    ).first()

    if not user:
        expired_user = User.objects.filter(otp=otp).first()
        if expired_user:
            raise OTPExpiredError("OTP has expired. Please request a new one.")
        raise InvalidOTPError("Invalid OTP code.")

    if user.is_locked_out:
        raise AccountLockedError(
            f"Account is locked due to multiple failed login attempts. "
            f"Please try again after "
            f"{settings.LOCKOUT_DURATION.total_seconds() / 60} minutes.",
        )

    user.verify_otp(otp)

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    logger.info("Successful login with OTP: %s", user.email)

    return OTPVerifyResult(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
    )
