from odin.codecs import dict_codec

from django.db.models import QuerySet

from oscar.core.loading import get_class, get_model, get_classes
from oscar_elasticsearch.search import settings

# this index name is retrived with get_class because of i18n but it might be removed later
(
    OSCAR_PRODUCTS_INDEX_NAME,
    OSCAR_PRODUCT_SEARCH_FIELDS,
    get_products_index_mapping,
    get_oscar_index_settings,
) = get_classes(
    "search.indexing.settings",
    [
        "OSCAR_PRODUCTS_INDEX_NAME",
        "OSCAR_PRODUCT_SEARCH_FIELDS",
        "get_products_index_mapping",
        "get_oscar_index_settings",
    ],
)
BaseElasticSearchApi = get_class("search.api.search", "BaseElasticSearchApi")
ESModelIndexer = get_class("search.indexing.indexer", "ESModelIndexer")
Product = get_model("catalogue", "Product")


class ProductElasticsearchIndex(BaseElasticSearchApi, ESModelIndexer):
    Model = Product
    INDEX_NAME = OSCAR_PRODUCTS_INDEX_NAME
    INDEX_MAPPING = get_products_index_mapping()
    INDEX_SETTINGS = get_oscar_index_settings()
    SEARCH_FIELDS = OSCAR_PRODUCT_SEARCH_FIELDS
    SUGGESTION_FIELD_NAME = settings.SUGGESTION_FIELD_NAME

    def get_filters(self, filters):
        if filters is not None:
            return filters

        return [{"term": {"is_public": True}}]

    def make_documents(self, objects):
        if not isinstance(objects, QuerySet):
            try:
                objects = Product.objects.filter(id__in=[o.id for o in objects])
            except:
                # pylint: disable=raise-missing-from
                raise ValueError(
                    "Argument 'objects' must be a QuerySet, as product_queryset_to_resources requires a QuerySet, got %s"
                    % type(objects)
                )

        from oscar_odin.mappings import catalogue

        ProductElasticSearchMapping = get_class(
            "search.mappings.products", "ProductElasticSearchMapping"
        )

        product_resources = catalogue.product_queryset_to_resources(objects)
        product_document_resources = ProductElasticSearchMapping.apply(
            product_resources
        )

        return dict_codec.dump(product_document_resources, include_type_field=False)
