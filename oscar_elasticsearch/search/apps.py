# pylint: disable=W0201
from django.urls import path
from django.utils.translation import gettext_lazy as _

from oscar.apps.search.apps import SearchConfig
from oscar.core.loading import get_class

from .constants import APP_LABEL


class OscarElasticSearchConfig(SearchConfig):
    label = APP_LABEL
    name = "oscar_elasticsearch.search"
    verbose_name = _("Elasticsearch")

    namespace = "search"

    # pylint: disable=W0201
    def ready(self):
        super().ready()
        self.autocomplete_view = get_class(
            "search.views.search", "CatalogueAutoCompleteView"
        )

        from .signal_handlers import register_signal_handlers

        register_signal_handlers()

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path(
                "autocomplete/", self.autocomplete_view.as_view(), name="autocomplete"
            ),
        ]
        return self.post_process_urls(urls)
