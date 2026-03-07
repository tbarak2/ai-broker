"""
Auth views — login (step 1), TOTP setup, TOTP activate, TOTP verify (step 2).

Login flow:
  1. POST /api/auth/login/         → validate password → return partial_token
  2a. GET  /api/auth/totp/setup/   → (first login) return QR code PNG as data-URL + secret
  2b. POST /api/auth/totp/activate/→ verify first code → activate 2FA → return full tokens
  2c. POST /api/auth/totp/verify/  → (subsequent logins) verify code → return full tokens
  3. POST /api/auth/token/refresh/ → rotate access token
  4. GET  /api/auth/me/            → current user info (requires full auth)
"""
import base64
import io
import logging
from datetime import timedelta

import pyotp
import qrcode
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView

from .models import TOTPSecret

logger = logging.getLogger(__name__)

PARTIAL_TOKEN_LIFETIME = timedelta(minutes=5)
TOTP_STAGE_CLAIM = "totp_stage"
TOTP_STAGE_PENDING = "pending"


def _make_partial_token(user: User) -> AccessToken:
    """Short-lived token only valid for TOTP setup/verify endpoints."""
    token = AccessToken.for_user(user)
    token.set_exp(lifetime=PARTIAL_TOKEN_LIFETIME)
    token[TOTP_STAGE_CLAIM] = TOTP_STAGE_PENDING
    return token


def _resolve_partial_token(token_str: str) -> User:
    """Parse and validate a partial token; raise ValueError on any problem."""
    try:
        token = AccessToken(token_str)
    except (TokenError, InvalidToken) as exc:
        raise ValueError("Invalid or expired session.") from exc
    if token.get(TOTP_STAGE_CLAIM) != TOTP_STAGE_PENDING:
        raise ValueError("Token is not a TOTP-stage token.")
    try:
        return User.objects.get(id=token["user_id"])
    except User.DoesNotExist as exc:
        raise ValueError("User not found.") from exc


def _issue_tokens(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {"id": user.id, "username": user.username, "email": user.email},
    }


# ── Step 1 ────────────────────────────────────────────────────────────────────

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({"detail": "Invalid credentials."}, status=400)

        partial_token = str(_make_partial_token(user))

        try:
            totp = user.totp_secret
            if totp.is_active:
                return Response({"totp_required": True, "partial_token": partial_token})
            # Secret exists but not yet activated → re-generate and require setup
        except TOTPSecret.DoesNotExist:
            pass

        return Response({"setup_required": True, "partial_token": partial_token})


# ── Step 2a — First-time TOTP setup ──────────────────────────────────────────

class TOTPSetupView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        partial_token_str = request.query_params.get("partial_token", "")
        try:
            user = _resolve_partial_token(partial_token_str)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=401)

        # Generate (or regenerate) secret
        secret = pyotp.random_base32()
        TOTPSecret.objects.update_or_create(
            user=user,
            defaults={"secret": secret, "is_active": False},
        )

        uri = pyotp.TOTP(secret).provisioning_uri(
            name=user.username, issuer_name="AI Broker"
        )

        # Build QR code as data-URL
        img = qrcode.make(uri)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

        return Response({
            "secret": secret,
            "qr_code": qr_data_url,
            "partial_token": partial_token_str,  # pass-through for convenience
        })


# ── Step 2b — Activate TOTP (first time) ─────────────────────────────────────

class TOTPActivateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        partial_token_str = request.data.get("partial_token", "")
        code = request.data.get("code", "").strip()

        try:
            user = _resolve_partial_token(partial_token_str)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=401)

        try:
            totp_secret = user.totp_secret
        except TOTPSecret.DoesNotExist:
            return Response({"detail": "No TOTP secret found. Please start setup again."}, status=400)

        if not pyotp.TOTP(totp_secret.secret).verify(code, valid_window=1):
            return Response({"detail": "Invalid code. Try again."}, status=400)

        totp_secret.is_active = True
        totp_secret.save(update_fields=["is_active"])

        logger.info("TOTP activated for user %s", user.username)
        return Response(_issue_tokens(user))


# ── Step 2c — Verify TOTP (subsequent logins) ────────────────────────────────

class TOTPVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        partial_token_str = request.data.get("partial_token", "")
        code = request.data.get("code", "").strip()

        try:
            user = _resolve_partial_token(partial_token_str)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=401)

        try:
            totp_secret = user.totp_secret
        except TOTPSecret.DoesNotExist:
            return Response({"detail": "2FA not configured."}, status=400)

        if not totp_secret.is_active:
            return Response({"detail": "2FA not activated."}, status=400)

        if not pyotp.TOTP(totp_secret.secret).verify(code, valid_window=1):
            return Response({"detail": "Invalid code. Try again."}, status=400)

        logger.info("Successful 2FA login for user %s", user.username)
        return Response(_issue_tokens(user))


# ── Token refresh (delegates to simplejwt) ────────────────────────────────────

class TokenRefreshView(BaseTokenRefreshView):
    permission_classes = [AllowAny]


# ── Current user ──────────────────────────────────────────────────────────────

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({"id": user.id, "username": user.username, "email": user.email})
