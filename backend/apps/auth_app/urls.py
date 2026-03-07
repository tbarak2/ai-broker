from django.urls import path
from .views import (
    LoginView,
    MeView,
    TOTPActivateView,
    TOTPSetupView,
    TOTPVerifyView,
    TokenRefreshView,
)

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/totp/setup/", TOTPSetupView.as_view(), name="auth-totp-setup"),
    path("auth/totp/activate/", TOTPActivateView.as_view(), name="auth-totp-activate"),
    path("auth/totp/verify/", TOTPVerifyView.as_view(), name="auth-totp-verify"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
]
