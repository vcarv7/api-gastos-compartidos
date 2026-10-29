"""Contract tests for the usuario API."""

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

REGISTER_URL = "/api/v1/usuario/register/"
TOKEN_URL = "/api/v1/usuario/token/"
REFRESH_URL = "/api/v1/usuario/token/refresh/"
ME_URL = "/api/v1/usuario/me/"
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


class LoginViewTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="victor", email="victor@mail.com", password=PASSWORD
        )

    def test_login_returns_token_pair(self):
        response = self.client.post(
            TOKEN_URL, {"username": "victor", "password": PASSWORD}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_rejects_bad_password(self):
        response = self.client.post(
            TOKEN_URL, {"username": "victor", "password": "incorrecta"}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_rejects_inactive_user(self):
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            TOKEN_URL, {"username": "victor", "password": PASSWORD}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_is_throttled(self):
        for _ in range(5):
            self.client.post(
                TOKEN_URL, {"username": "victor", "password": "incorrecta"}
            )

        response = self.client.post(
            TOKEN_URL, {"username": "victor", "password": "incorrecta"}
        )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_refresh_rotates_and_blacklists_the_old_token(self):
        first = self.client.post(
            TOKEN_URL, {"username": "victor", "password": PASSWORD}
        ).data["refresh"]

        rotated = self.client.post(REFRESH_URL, {"refresh": first})
        self.assertEqual(rotated.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", rotated.data)

        reused = self.client.post(REFRESH_URL, {"refresh": first})
        self.assertEqual(reused.status_code, status.HTTP_401_UNAUTHORIZED)


class MeViewTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="victor", email="victor@mail.com", password=PASSWORD
        )
        access = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_requires_authentication(self):
        self.client.credentials()

        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_current_user(self):
        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "victor")
        self.assertEqual(response.data["id"], str(self.user.id))
        self.assertNotIn("password", response.data)

    def test_rejects_token_after_password_change(self):
        self.user.set_password("OtraClave#2026")
        self.user.save()

        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_rejects_token_for_deactivated_user(self):
        self.user.is_active = False
        self.user.save()

        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
