"""Settings shared by every environment.

The environment modules (``local`` and ``produccion``) start with
``from .base import *`` and override only what differs. Nothing here may hold a
secret: every sensitive value is read from an environment variable so the same
code runs unchanged everywhere.
"""

import os
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
    "DEFAULT_THROTTLE_RATES": {"anon": "20/min"},
}
