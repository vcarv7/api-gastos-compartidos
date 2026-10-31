"""Settings shared by every environment.

The environment modules (``local`` and ``produccion``) start with
``from .base import *`` and override only what differs. Nothing here may hold a
secret: every sensitive value is read from an environment variable so the same
code runs unchanged everywhere.
"""

import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent


# --- Environment helpers ---------------------------------------------------


def env(name, default=""):
    """Return an environment variable as a stripped string."""
    return os.environ.get(name, default).strip()


def env_list(name, default=""):
    """Return a comma-separated environment variable as a list of values."""
    return [item.strip() for item in env(name, default).split(",") if item.strip()]


def env_bool(name, default=False):
    """Return an environment variable as a boolean."""
    return env(name, str(default)).lower() in {"1", "true", "yes", "on"}


def required(name):
    """Return an environment variable, refusing to boot when it is missing."""
    value = env(name)
    if not value:
        raise ImproperlyConfigured(
            f"The {name} environment variable is required in this environment."
        )
    return value


# --- Security --------------------------------------------------------------

# SECRET_KEY has no default on purpose: each environment module decides how it
# is provided, so a missing key can never silently fall back to a shared one.
SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")


# --- Application definition ------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

DRF_APPS = [
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.usuario",
]

INSTALLED_APPS = DJANGO_APPS + DRF_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --- Database --------------------------------------------------------------

# Development default. ``produccion`` replaces this with PostgreSQL read from
# the environment.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Authentication --------------------------------------------------------

# Declared before the first migration on purpose: changing the user model
# afterwards means dropping the database and every migration.
AUTH_USER_MODEL = "usuario.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# --- Internationalization --------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# --- Static and media files ------------------------------------------------

STATIC_URL = "static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"

MEDIA_ROOT = BASE_DIR / "media"


# --- Email -----------------------------------------------------------------

EMAIL_BACKEND = env(
    "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = int(env("EMAIL_PORT", "587"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "no-reply@localhost")


# --- Django REST Framework -------------------------------------------------

# Throttle scopes are declared here so views can name a scope and stop caring
# about the numbers. AnonRateThrottle raises ImproperlyConfigured at request
# time when its scope is missing.
REST_FRAMEWORK = {
    # Without this, every view keeps DRF's built-in AutoSchema and the
    # generator aborts on the drf-spectacular documentation views themselves.
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # JWT only. A browser session must not authenticate an API request:
        # with SessionAuthentication in this list, every unsafe request sent
        # from Swagger UI is authenticated by the admin cookie and then rejected
        # by CSRF, because Swagger cannot attach an X-CSRFToken header.
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/min",
        "login": "5/min",
    },
}


# --- JWT -------------------------------------------------------------------

# Tokens are returned in the JSON body: clients send them back as
# "Authorization: Bearer <access>". No cookie transport, therefore no CSRF.
SIMPLE_JWT = {
    # Short-lived access keeps the blast radius of a leaked token small.
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # A rotated refresh is blacklisted, so a stolen one dies on reuse.
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    # Without this last_login stays None forever.
    "UPDATE_LAST_LOGIN": True,
    # Embeds a hash of the password: changing it revokes every older token.
    "CHECK_REVOKE_TOKEN": True,
}


# --- API documentation -----------------------------------------------------

SPECTACULAR_SETTINGS = {
    "TITLE": "API Gastos Compartidos",
    "DESCRIPTION": "Gestión de gastos compartidos entre grupos.",
    "VERSION": "1.0.0",
    # Group and tag operations by API version.
    "SCHEMA_PATH_PREFIX": "/api/v1",
    # Do not document the schema endpoint itself.
    "SERVE_INCLUDE_SCHEMA": False,
    # Separate request and response components so neither lies about required
    # fields (``id`` is required on the way out, absent on the way in).
    "COMPONENT_SPLIT_REQUEST": True,
    # The schema maps the whole API surface, so it is staff-only.
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAdminUser"],
    # The documentation pages are HTML rendered for a browser, so they keep
    # session authentication even though the API itself is JWT-only.
    "SERVE_AUTHENTICATION": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    # Pinned on purpose. Both default to "@latest", and ReDoc 3 switched to an
    # ES module that a classic <script> tag cannot execute, which rendered
    # /api/redoc/ blank. A floating tag means the docs can break without a
    # single change in this repository.
    "SWAGGER_UI_DIST": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.34.1",
    "REDOC_DIST": "https://cdn.jsdelivr.net/npm/redoc@2.1.5",
}
