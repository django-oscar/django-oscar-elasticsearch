from django.urls import path

from oscar.core.application import Application as BaseApplication
from oscar.core.loading import get_class
from .constants import APP_LABEL

CatalogueSearchView = get_class("search.views", "CatalogueSearchView")
CatalogueAutoCompleteView = get_class("search.views", "CatalogueAutoCompleteView")


class Application(BaseApplication):
    name = APP_LABEL


application = Application()
