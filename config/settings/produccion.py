"""Production settings.

Everything sensitive comes from the environment and the application refuses to
start when a required value is missing. Report the problem at boot, not at the
first request that happens to need it.
"""

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import env, env_bool, env_list, required

# Never enable DEBUG in production: it leaks settings, SQL and source.
DEBUG = False

SECRET_KEY = required("SECRET_KEY")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "The ALLOWED_HOSTS environment variable is required in production."
    )


# --- Database --------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": required("DB_NAME"),
        "USER": required("DB_USER"),
        "PASSWORD": required("DB_PASSWORD"),
        "HOST": required("DB_HOST"),
        "PORT": env("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}


# --- HTTPS and cookies -----------------------------------------------------

SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

# Only keep this when the app runs behind a reverse proxy that sets the header.
if env_bool("USE_X_FORWARDED_PROTO", True):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_HSTS_SECONDS = int(env("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)

SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
