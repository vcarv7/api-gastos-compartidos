"""Development settings.

Usable with no environment variables at all: a new contributor clones the
repository, runs ``uv sync`` and starts the server.
"""

from .base import *  # noqa: F403
from .base import env, env_bool, env_list

DEBUG = env_bool("DEBUG", True)

# Insecure on purpose. Production refuses to start without a real key.
SECRET_KEY = env("SECRET_KEY", "django-insecure-local-only-do-not-ship")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]")

# Print emails to the console instead of sending them.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
