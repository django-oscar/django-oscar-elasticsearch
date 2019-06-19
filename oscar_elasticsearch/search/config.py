from django.conf.urls import url
from django.utils.translation import gettext_lazy as _

from oscar.apps.search import apps
from oscar.core.loading import get_class


class SearchConfig(apps.SearchConfig):
    label = "search"
    name = "oscar_elasticsearch.search"
    verbose_name = _("Search")

    def ready(self):
        from .signal_handlers import register_signal_handlers
        
        register_signal_handlers()
        super().ready()

        self.catalogue_search_view = get_class("search.views", "CatalogueSearchView")
        self.catalogue_auto_complete_view = get_class("search.views", "CatalogueAutoCompleteView")

    def get_urls(self):
        urls = [
            url(r"^$", self.catalogue_search_view.as_view(), name="search"),
            url(
                r"^autocomplete/$",
                self.catalogue_auto_complete_view.as_view(),
                name="autocomplete",
            ),
        ]
        return self.post_process_urls(urls)
