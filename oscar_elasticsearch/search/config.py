from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SearchConfig(AppConfig):
    label = "search"
    name = "oscar_elasticsearch.search"
    verbose_name = _("Search")
