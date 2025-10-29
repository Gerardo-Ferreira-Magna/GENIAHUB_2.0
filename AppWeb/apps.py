from django.apps import AppConfig


class AppwebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'AppWeb'

    def ready(self):
        # registrar signals
        from . import signals   