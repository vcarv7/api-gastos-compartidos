"""Custom user model for the usuario app.

Login, permissions and superuser creation are delegated to Django's
``AbstractUser``. This model only adds the project's own fields:

- a UUIDv7 primary key, so user identifiers cannot be enumerated,
- a case-insensitively unique email address,
- optional contact details.
"""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class User(AbstractUser):
    # ``password``, ``username``, ``is_active``, ``is_staff``, ``is_superuser``,
    # ``date_joined`` and ``last_login`` are inherited from AbstractUser.
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to="users/photos/", blank=True, null=True)

    class Meta:
        constraints = [
            # ``unique=True`` above compares raw bytes, so "Victor@mail.com" and
            # "victor@mail.com" would both be accepted. This functional index
            # makes uniqueness case-insensitive at the database level.
            models.UniqueConstraint(Lower("email"), name="unique_email_ci"),
        ]

    def __str__(self):
        return self.username
