"""Contract tests for the usuario API."""

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

REGISTER_URL = "/api/v1/usuario/register/"
TOKEN_URL = "/api/v1/usuario/token/"
REFRESH_URL = "/api/v1/usuario/token/refresh/"
ME_URL = "/api/v1/usuario/me/"
SCHEMA_URL = "/api/schema/"
DOCS_URL = "/api/docs/"
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


class DocumentationAccessTests(APITestCase):
    """The docs authenticate with SessionAuthentication, which defines no
    authenticate_header. DRF can only answer 401 when an authenticator can send
    a WWW-Authenticate challenge, so anonymous access is refused with 403."""

    def setUp(self):
        cache.clear()

    def test_schema_is_not_public(self):
        response = self.client.get(SCHEMA_URL)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_swagger_ui_is_not_public(self):
        response = self.client.get(DOCS_URL)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_read_the_schema(self):
        staff = User.objects.create_user(
            username="staff",
            email="staff@mail.com",
            password=PASSWORD,
            is_staff=True,
        )
        self.client.force_authenticate(staff)

        response = self.client.get(SCHEMA_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.content.decode()
        self.assertIn("/api/v1/usuario/register/", body)
        self.assertIn("/api/v1/usuario/me/", body)


class SwaggerUiRegressionTests(APITestCase):
    """A staff session must not leak into the API itself."""

    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(
            username="staff",
            email="staff@mail.com",
            password=PASSWORD,
            is_staff=True,
        )

    def test_register_works_from_a_logged_in_browser(self):
        # Exactly what Swagger UI sends: session cookie, no CSRF header.
        browser = Client(HTTP_HOST="localhost", enforce_csrf_checks=True)
        browser.force_login(self.staff)

        response = browser.post(
            REGISTER_URL,
            {"username": "victor", "email": "Victor@Mail.com", "password": PASSWORD},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="victor").exists())

    def test_documentation_opens_with_a_real_session(self):
        # force_login runs the authenticator; force_authenticate bypasses it.
        browser = Client(HTTP_HOST="localhost")
        browser.force_login(self.staff)

        self.assertEqual(browser.get(SCHEMA_URL).status_code, status.HTTP_200_OK)
        self.assertEqual(browser.get(DOCS_URL).status_code, status.HTTP_200_OK)


class DocumentationGroupingTests(APITestCase):
    """Operations must be grouped by domain, not by folder."""

    def setUp(self):
        cache.clear()
        staff = User.objects.create_user(
            username="staff",
            email="staff@mail.com",
            password=PASSWORD,
            is_staff=True,
        )
        self.client.force_authenticate(staff)

    def test_operations_are_grouped_into_two_tags(self):
        response = self.client.get(SCHEMA_URL, {"format": "json"})

        paths = response.json()["paths"]
        grouping = {
            path: operation[method]["tags"][0]
            for path, operation in paths.items()
            for method in operation
        }

        self.assertEqual(
            grouping,
            {
                "/api/v1/usuario/register/": "Cuentas",
                "/api/v1/usuario/me/": "Cuentas",
                "/api/v1/usuario/token/": "Sesiones",
                "/api/v1/usuario/token/refresh/": "Sesiones",
                "/api/v1/usuario/token/verify/": "Sesiones",
                "/api/v1/usuario/token/blacklist/": "Sesiones",
            },
        )
