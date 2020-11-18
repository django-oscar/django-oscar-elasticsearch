from django.urls import path
from django.utils.translation import ugettext_lazy as _

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class

from .constants import APP_LABEL


class OscarElasticSearchConfig(OscarConfig):
    label = APP_LABEL
    name = "oscar_elasticsearch.search"
    verbose_name = _("Elasticsearch")

    def ready(self):
        self.search_view = get_class("search.views", "CatalogueSearchView")
        self.autocomplete_view = get_class("search.views", "CatalogueAutoCompleteView")

        from .signal_handlers import register_signal_handlers

        register_signal_handlers()

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path("", self.search_view.as_view(), name="search"),
            path(
                "autocomplete/", self.autocomplete_view.as_view(), name="autocomplete"
            ),
        ]
        return self.post_process_urls(urls)
