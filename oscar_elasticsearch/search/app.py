from django.urls import path

from oscar.core.application import Application as BaseApplication
from oscar.core.loading import get_class
from .constants import APP_LABEL

CatalogueSearchView = get_class("search.views", "CatalogueSearchView")
CatalogueAutoCompleteView = get_class("search.views", "CatalogueAutoCompleteView")


class Application(BaseApplication):
    name = APP_LABEL

    def get_urls(self):
        urls = [
            path("", CatalogueSearchView.as_view(), name="search"),
            path(
                "autocomplete/",
                CatalogueAutoCompleteView.as_view(),
                name="autocomplete",
            ),
        ]
        return self.post_process_urls(urls)


application = Application()
