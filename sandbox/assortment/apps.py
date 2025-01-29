from django.apps import AppConfig


class AssortmentConfig(AppConfig):
    name = "assortment"
    verbose_name = "Assortment"

    def ready(self):
        from . import index
