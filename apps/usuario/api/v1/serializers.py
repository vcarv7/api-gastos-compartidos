"""Serializers for version 1 of the usuario API."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Create an account from a username, an email address and a password.

    Uniqueness is checked case-insensitively here for a friendly 400 response.
    The database constraints remain the last line of defence: this validation
    can be bypassed by concurrent requests and by every path that does not go
    through this serializer.
    """

    password = serializers.CharField(
        write_only=True,
        # DRF trims whitespace on CharField by default. Silently trimming a
        # password means storing something the user did not type.
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")
        read_only_fields = ("id",)
        extra_kwargs = {
            # Replace DRF's auto-generated UniqueValidator so every uniqueness
            # message comes from validate_username() below. The format
            # validator has to be re-declared because setting ``validators``
            # replaces the whole list, not just the unique check.
            "username": {"validators": [UnicodeUsernameValidator()]},
            "email": {"validators": []},
        }

    def validate_username(self, value):
        value = value.strip()
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "This email address is already registered."
            )
        return value

    def validate(self, attrs):
        # Object level on purpose: UserAttributeSimilarityValidator compares the
        # password against the username and the email, so it needs both. Called
        # without a user instance it silently validates nothing.
        candidate = User(username=attrs["username"], email=attrs["email"])
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": exc.messages})
        return attrs

    def create(self, validated_data):
        try:
            with transaction.atomic():
                return User.objects.create_user(**validated_data)
        except IntegrityError:
            # Two concurrent requests can both pass the checks above. The
            # database constraint wins; turn it into a 400 instead of a 500.
            raise serializers.ValidationError(
                {"detail": "An account with these details already exists."}
            )
