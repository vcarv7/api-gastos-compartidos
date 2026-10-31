"""URL routes for version 1 of the usuario API."""

from django.urls import path
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import LoginView, MeView, RegisterView


# These three views belong to simplejwt, so the documentation tag cannot be
# declared on the view itself. extend_schema_view patches a copy of the class.
def _tagged_for_docs(view):
    return extend_schema_view(post=extend_schema(tags=["Sesiones"]))(view)


RefreshDocs = _tagged_for_docs(TokenRefreshView)
VerifyDocs = _tagged_for_docs(TokenVerifyView)
BlacklistDocs = _tagged_for_docs(TokenBlacklistView)

app_name = "usuario_v1"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("token/", LoginView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", RefreshDocs.as_view(), name="token_refresh"),
    path("token/verify/", VerifyDocs.as_view(), name="token_verify"),
    path("token/blacklist/", BlacklistDocs.as_view(), name="token_blacklist"),
    path("me/", MeView.as_view(), name="me"),
]
