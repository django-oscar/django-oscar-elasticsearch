from django.urls import path
from django.utils.translation import ugettext_lazy as _

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class

from .constants import APP_LABEL


class OscarElasticSearchConfig(OscarConfig):
    label = APP_LABEL
    name = "oscar_elasticsearch.search"
    verbose_name = _("Elasticsearch")

    namespace = "search"
