from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        print("starting scheduler")
        from .site_scheduler import site_updater
        site_updater.start()