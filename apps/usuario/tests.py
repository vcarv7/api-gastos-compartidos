"""Contract tests for the usuario API."""

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

REGISTER_URL = "/api/v1/usuario/register/"
PASSWORD = "Zx9#mundoLargo"


class RegisterViewTests(APITestCase):
    def setUp(self):
        # Throttle counters live in the cache and would leak between tests.
        cache.clear()

    def test_creates_account(self):
        response = self.client.post(
            REGISTER_URL,
            {"username": "victor", "email": "Victor@Mail.com", "password": PASSWORD},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)

        user = User.objects.get(username="victor")
        self.assertEqual(user.email, "victor@mail.com")
        self.assertTrue(user.check_password(PASSWORD))
        self.assertEqual(str(user.id), response.data["id"])

    def test_rejects_duplicate_email_case_insensitive(self):
        User.objects.create_user(
            username="uno", email="victor@mail.com", password=PASSWORD
        )

        response = self.client.post(
            REGISTER_URL,
            {"username": "dos", "email": "VICTOR@mail.com", "password": PASSWORD},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_rejects_duplicate_username_case_insensitive(self):
        User.objects.create_user(
            username="victor", email="uno@mail.com", password=PASSWORD
        )

        response = self.client.post(
            REGISTER_URL,
            {"username": "VICTOR", "email": "dos@mail.com", "password": PASSWORD},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_rejects_weak_password(self):
        response = self.client.post(
            REGISTER_URL,
            {"username": "victor", "email": "victor@mail.com", "password": "123"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_rejects_invalid_email(self):
        response = self.client.post(
            REGISTER_URL,
            {"username": "victor", "email": "no-es-email", "password": PASSWORD},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_rejects_missing_fields(self):
        response = self.client.post(REGISTER_URL, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertCountEqual(response.data.keys(), ["username", "email", "password"])
