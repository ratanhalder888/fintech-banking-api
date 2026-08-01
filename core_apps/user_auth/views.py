from typing import Any, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from loguru import logger
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from drf_spectacular.utils import extend_schema
from .serializers import LoginSerializer, OTPSerializer
from .services import (
    AccountLockedError,
    InvalidCredentialsError,
    InvalidOTPError,
    LoginError,
    OTPExpiredError,
    login_initiate,
    otp_verify,
)

User = get_user_model()


# ------------------------------------------------------------------
# Cookie helpers (pure HTTP concern — stays in the view layer)
# ------------------------------------------------------------------

def set_auth_cookies(
    response: Response, access_token: str, refresh_token: Optional[str] = None
) -> None:
    """Set JWT cookies on the response object."""
    access_token_lifetime = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()
    cookie_settings = {
        "path": settings.COOKIE_PATH,
        "secure": settings.COOKIE_SECURE,
        "httponly": settings.COOKIE_HTTPONLY,
        "samesite": settings.COOKIE_SAMESITE,
        "max_age": access_token_lifetime,
    }
    response.set_cookie("access", access_token, **cookie_settings)

    if refresh_token:
        refresh_token_lifetime = settings.SIMPLE_JWT[
            "REFRESH_TOKEN_LIFETIME"
        ].total_seconds()
        refresh_cookie_settings = cookie_settings.copy()
        refresh_cookie_settings["max_age"] = refresh_token_lifetime
        response.set_cookie("refresh", refresh_token, **refresh_cookie_settings)

    logged_in_cookie_settings = cookie_settings.copy()
    logged_in_cookie_settings["httponly"] = False
    response.set_cookie("logged_in", "true", **logged_in_cookie_settings)


# ------------------------------------------------------------------
# Views (thin — HTTP concerns only, no business logic)
# ------------------------------------------------------------------

class LoginView(APIView):
    """
    POST /api/v1/auth/login/

    Validates email + password and sends an OTP to the user's email.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={200: Any, 400: Any, 403: Any},
    )
    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = login_initiate(
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
            )
        except InvalidCredentialsError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except AccountLockedError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {"success": "OTP sent to your email", "email": result.email},
            status=status.HTTP_200_OK,
        )


class OTPVerifyView(APIView):
    """
    POST /api/v1/auth/verify-otp/

    Validates the OTP and returns JWT tokens (set as httpOnly cookies).
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=OTPSerializer,
        responses={200: Any},
    )
    def post(self, request: Request) -> Response:
        serializer = OTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = otp_verify(otp=serializer.validated_data["otp"])
        except InvalidOTPError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except OTPExpiredError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except AccountLockedError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        response = Response(
            {
                "success": "Login successful. Now add your profile information, "
                "so that we can create an account for you",
            },
            status=status.HTTP_200_OK,
        )
        set_auth_cookies(
            response,
            access_token=result.access_token,
            refresh_token=result.refresh_token,
        )
        return response


class CustomTokenRefreshView(TokenRefreshView):
    """POST /api/v1/auth/refresh/"""

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        refresh_token = request.COOKIES.get("refresh")

        if refresh_token:
            request.data["refresh"] = refresh_token

        refresh_res = super().post(request, *args, **kwargs)

        if refresh_res.status_code == status.HTTP_200_OK:
            access_token = refresh_res.data.get("access")
            refresh_token = refresh_res.data.get("refresh")

            if access_token and refresh_token:
                set_auth_cookies(
                    refresh_res,
                    access_token=access_token,
                    refresh_token=refresh_token,
                )

                refresh_res.data.pop("access", None)
                refresh_res.data.pop("refresh", None)

                refresh_res.data["message"] = "Access tokens refreshed successfully."
            else:
                logger.error(
                    "Access or refresh token not found in refresh response data"
                )

        return refresh_res


class LogoutAPIView(APIView):
    """POST /api/v1/auth/logout/"""

    def post(self, request: Request) -> Response:
        refresh_token = request.COOKIES.get("refresh") or request.data.get("refresh")

        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                logger.warning(
                    "Logout requested with an invalid or already blacklisted "
                    "refresh token"
                )

        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie("access")
        response.delete_cookie("refresh")
        response.delete_cookie("logged_in")
        return response