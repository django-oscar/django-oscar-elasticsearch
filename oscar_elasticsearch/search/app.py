from django.conf.urls import url

from oscar.core.application import Application as BaseApplication
from oscar.core.loading import get_class

CatalogueSearchView = get_class("search.views", "CatalogueSearchView")
CatalogueAutoCompleteView = get_class("search.views", "CatalogueAutoCompleteView")


class Application(BaseApplication):
    name = "search"

    def get_urls(self):
        urls = [
            url(r"^$", CatalogueSearchView.as_view(), name="search"),
            url(
                r"^autocomplete/$",
                CatalogueAutoCompleteView.as_view(),
                name="autocomplete",
            ),
        ]
        return self.post_process_urls(urls)


application = Application()
