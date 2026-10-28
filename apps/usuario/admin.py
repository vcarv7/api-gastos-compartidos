"""Admin registration for the custom user model."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Extend Django's UserAdmin instead of rewriting it.

    Inheriting keeps us aligned with upstream fields (``usable_password`` and
    friends) that newer Django versions add to these tuples.
    """

    list_display = ("username", "email", "phone", "is_staff")
    search_fields = ("username", "email", "phone")

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Contact", {"fields": ("phone", "photo")}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Contact", {"fields": ("email", "phone", "photo")}),
    )
