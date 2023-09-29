from odin.codecs import dict_codec

from django.core.management.base import BaseCommand

from oscar.core.loading import get_class, get_model

from oscar_odin.mappings import catalogue

from oscar_elasticsearch.search.mappings import ProductElasticSearchMapping

Indexer = get_class("search.indexing", "Indexer")
OSCAR_INDEX_NAME = get_class("search.settings", "OSCAR_INDEX_NAME")
OSCAR_INDEX_MAPPING = get_class("search.settings", "OSCAR_INDEX_MAPPING")
OSCAR_INDEX_SETTINGS = get_class("search.settings", "OSCAR_INDEX_SETTINGS")

Product = get_model("catalogue", "Product")


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        odin_resources = catalogue.product_queryset_to_resources(
            Product.objects.browsable()
        )

        indexer = Indexer(
            OSCAR_INDEX_NAME,
            OSCAR_INDEX_MAPPING,
            OSCAR_INDEX_SETTINGS,
        )

        es_resources = ProductElasticSearchMapping.apply(
            odin_resources, context={"_index": indexer.alias_name, "_type": "doc"}
        )
        indexer.execute(dict_codec.dump(es_resources, include_type_field=False))
