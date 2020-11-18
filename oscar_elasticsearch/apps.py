from django.utils.translation import ugettext_lazy as _

from oscar.core.application import OscarConfig


class OscarElasticSearchConfig(OscarConfig):
    label = "oscar_elasticsearch"
    name = "oscar_elasticsearch"
    verbose_name = _("Elasticsearch")

    def ready(self):
        from .signal_handlers import register_signal_handlers

        register_signal_handlers()
