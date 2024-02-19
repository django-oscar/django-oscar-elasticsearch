from odin.codecs import dict_codec

from django.core.management.base import BaseCommand

from oscar.core.loading import get_class, get_model

from oscar_odin.mappings import catalogue

Indexer = get_class("search.indexing", "Indexer")

OSCAR_CATEGORIES_INDEX_NAME = get_class(
    "search.settings", "OSCAR_CATEGORIES_INDEX_NAME"
)
OSCAR_CATEGORIES_INDEX_MAPPING = get_class(
    "search.settings", "OSCAR_CATEGORIES_INDEX_MAPPING"
)
OSCAR_INDEX_SETTINGS = get_class("search.settings", "OSCAR_INDEX_SETTINGS")

CategoryElasticSearchMapping = get_class(
    "search.mappings.categories", "CategoryElasticSearchMapping"
)

Category = get_model("catalogue", "Category")


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("--" * 25)
        category_resources = catalogue.CategoryToResource.apply(
            Category.objects.browsable()
        )

        indexer = Indexer(
            OSCAR_CATEGORIES_INDEX_NAME,
            OSCAR_CATEGORIES_INDEX_MAPPING,
            OSCAR_INDEX_SETTINGS,
        )

        category_resources = CategoryElasticSearchMapping.apply(
            category_resources, context={"_index": indexer.alias_name, "_type": "doc"}
        )

        indexer.execute(dict_codec.dump(category_resources, include_type_field=False))
        print("Finished indexing %s categories" % len(category_resources))
