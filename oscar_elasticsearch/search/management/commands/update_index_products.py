from odin.codecs import dict_codec

from django.core.management.base import BaseCommand

from oscar.core.loading import get_class, get_model

from oscar_odin.mappings import catalogue

Indexer = get_class("search.indexing", "Indexer")

OSCAR_PRODUCTS_INDEX_NAME = get_class("search.settings", "OSCAR_PRODUCTS_INDEX_NAME")
OSCAR_PRODUCTS_INDEX_MAPPING = get_class(
    "search.settings", "OSCAR_PRODUCTS_INDEX_MAPPING"
)
OSCAR_INDEX_SETTINGS = get_class("search.settings", "OSCAR_INDEX_SETTINGS")

ProductElasticSearchMapping = get_class(
    "search.mappings.products", "ProductElasticSearchMapping"
)

Product = get_model("catalogue", "Product")


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("--" * 25)
        product_resources = catalogue.product_queryset_to_resources(
            Product.objects.browsable()
        )

        indexer = Indexer(
            OSCAR_PRODUCTS_INDEX_NAME,
            OSCAR_PRODUCTS_INDEX_MAPPING,
            OSCAR_INDEX_SETTINGS,
        )

        product_resources = ProductElasticSearchMapping.apply(
            product_resources, context={"_index": indexer.alias_name, "_type": "doc"}
        )

        indexer.execute(dict_codec.dump(product_resources, include_type_field=False))
        print("Finished indexing %s products" % len(product_resources))
