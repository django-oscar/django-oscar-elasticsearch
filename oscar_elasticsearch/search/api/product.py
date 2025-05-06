from odin.codecs import dict_codec

from django.db.models import QuerySet, Count, Subquery, OuterRef, IntegerField
from django.utils import timezone

from dateutil.relativedelta import relativedelta

from oscar.core.loading import get_class, get_model, get_classes
from oscar_elasticsearch.search import settings

from oscar_elasticsearch.search.utils import get_category_ancestors

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
Category = get_model("catalogue", "Category")
Line = get_model("order", "Line")


class ProductElasticsearchIndex(BaseElasticSearchApi, ESModelIndexer):
    Model = Product
    INDEX_NAME = OSCAR_PRODUCTS_INDEX_NAME
    INDEX_MAPPING = get_products_index_mapping()
    INDEX_SETTINGS = get_oscar_index_settings()
    SEARCH_FIELDS = OSCAR_PRODUCT_SEARCH_FIELDS
    SUGGESTION_FIELD_NAME = settings.SUGGESTION_FIELD_NAME
    context = {}

    def get_filters(self, filters):
        if filters is not None:
            return filters

        return [{"term": {"is_public": True}}]

    def make_documents(self, objects):
        if "category_titles" not in self.context:
            self.context["category_titles"] = dict(
                Category.objects.values_list("id", "name")
            )
        if "category_ancestors" not in self.context:
            self.context["category_ancestors"] = get_category_ancestors()

        if not isinstance(objects, QuerySet):
            try:
                objects = Product.objects.filter(id__in=[o.id for o in objects])
            except:
                # pylint: disable=raise-missing-from
                raise ValueError(
                    "Argument 'objects' must be a QuerySet, as product_queryset_to_resources requires a QuerySet, got %s"
                    % type(objects)
                )

        product_queryset_to_resources = get_class(
            "oscar_odin.mappings.helpers", "product_queryset_to_resources"
        )

        ProductElasticSearchMapping = get_class(
            "search.mappings.products", "ProductElasticSearchMapping"
        )

        # Annotate the queryset with popularity to avoid the need of n+1 queries
        objects = objects.annotate(
            popularity=Subquery(
                Line.objects.filter(
                    product=OuterRef("pk"),
                    order__date_placed__gte=timezone.now()
                    - relativedelta(months=settings.MONTHS_TO_RUN_ANALYTICS),
                )
                .values("product")
                .annotate(count=Count("id"))
                .values("count"),
                output_field=IntegerField(),
            )
        )

        product_resources = product_queryset_to_resources(
            objects, include_children=True
        )
        product_document_resources = ProductElasticSearchMapping.apply(
            product_resources, self.context
        )

        return dict_codec.dump(product_document_resources, include_type_field=False)
