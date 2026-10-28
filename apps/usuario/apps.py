from django.apps import AppConfig


class UsuarioConfig(AppConfig):
    # The app lives in the ``apps`` package, so the dotted path is required here.
    # The label stays "usuario", which is what AUTH_USER_MODEL and friends use.
    name = "apps.usuario"
    verbose_name = "Usuarios"
