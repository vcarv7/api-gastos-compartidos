"""URL routes for version 1 of the usuario API."""

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import LoginView, MeView, RegisterView

app_name = "usuario_v1"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("token/", LoginView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("token/blacklist/", TokenBlacklistView.as_view(), name="token_blacklist"),
    path("me/", MeView.as_view(), name="me"),
]
