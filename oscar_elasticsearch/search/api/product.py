from odin.codecs import dict_codec

from django.db import transaction

from oscar.core.loading import get_class, get_model

from oscar_elasticsearch.search import settings

OSCAR_PRODUCTS_INDEX_NAME = get_class(
    "search.indexing.settings", "OSCAR_PRODUCTS_INDEX_NAME"
)
get_products_index_mapping = get_class(
    "search.indexing.settings", "get_products_index_mapping"
)
get_oscar_index_settings = get_class(
    "search.indexing.settings", "get_oscar_index_settings"
)

OSCAR_INDEX_SETTINGS = get_oscar_index_settings()

BaseElasticSearchApi = get_class("search.api.search", "BaseElasticSearchApi")
ESModelIndexer = get_class("search.indexing.indexer", "ESModelIndexer")

Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")


class ProductElasticSearchApi(BaseElasticSearchApi, ESModelIndexer):
    INDEX_NAME = OSCAR_PRODUCTS_INDEX_NAME
    INDEX_MAPPING = get_products_index_mapping()
    INDEX_SETTINGS = OSCAR_INDEX_SETTINGS
    Model = Product
    SEARCH_FIELDS = settings.SEARCH_FIELDS
    SUGGESTION_FIELD_NAME = settings.SUGGESTION_FIELD_NAME

    # def get_default_filters(self):
    #        return [{"term": {"is_public": True}}]

    def get_es_data_from_objects(self, object_ids):
        from oscar_odin.mappings import catalogue

        ProductElasticSearchMapping = get_class(
            "search.mappings.products", "ProductElasticSearchMapping"
        )

        with transaction.atomic():
            products = Product.objects.filter(pk__in=object_ids).select_for_update()

            product_resources = catalogue.product_queryset_to_resources(products)

            product_resources = ProductElasticSearchMapping.apply(product_resources)

            return dict_codec.dump(product_resources, include_type_field=False)
