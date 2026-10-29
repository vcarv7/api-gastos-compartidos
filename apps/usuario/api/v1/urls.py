"""URL routes for version 1 of the usuario API."""

from django.urls import path

from .views import RegisterView

app_name = "usuario_v1"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
]
