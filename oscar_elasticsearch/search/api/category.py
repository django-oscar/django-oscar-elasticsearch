from odin.codecs import dict_codec

from django.db import transaction

from oscar.core.loading import get_class, get_model

from oscar_elasticsearch.search import settings

OSCAR_CATEGORIES_INDEX_NAME = get_class(
    "search.indexing.settings", "OSCAR_CATEGORIES_INDEX_NAME"
)
get_categories_index_mapping = get_class(
    "search.indexing.settings", "get_categories_index_mapping"
)
get_oscar_index_settings = get_class(
    "search.indexing.settings", "get_oscar_index_settings"
)


OSCAR_INDEX_SETTINGS = get_oscar_index_settings()

BaseElasticSearchApi = get_class("search.api.search", "BaseElasticSearchApi")
ESModelIndexer = get_class("search.indexing.indexer", "ESModelIndexer")

Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")


class CategoryElasticSearchApi(BaseElasticSearchApi, ESModelIndexer):
    INDEX_NAME = OSCAR_CATEGORIES_INDEX_NAME
    INDEX_MAPPING = get_categories_index_mapping()
    INDEX_SETTINGS = OSCAR_INDEX_SETTINGS
    Model = Category

    def get_es_data_from_objects(self, object_ids):
        from oscar_odin.mappings import catalogue

        CategoryMapping = get_class("search.mappings.categories", "CategoryMapping")

        with transaction.atomic():
            categories = Category.objects.filter(pk__in=object_ids).select_for_update()

            category_resources = catalogue.CategoryToResource.apply(categories)

            category_resources = CategoryMapping.apply(category_resources)

            return dict_codec.dump(category_resources, include_type_field=False)
