import odin

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.html import strip_tags

from dateutil.relativedelta import relativedelta

from oscar.core.loading import get_model, get_class

from oscar_odin.mappings._common import OscarBaseMapping
from oscar_odin.resources.catalogue import (
    Product as ProductResource,
    Category as CategoryResource,
)

from oscar_elasticsearch.search.constants import (
    ES_CTX_PUBLIC,
    ES_CTX_AVAILABLE,
    ES_CTX_BROWSABLE,
)
from oscar_elasticsearch.search import settings

Product = get_model("catalogue", "Product")
Line = get_model("order", "Line")

OscarElasticSearchResourceMixin = get_class(
    "search.mappings.mixins", "OscarElasticSearchResourceMixin"
)
get_attributes_to_index = get_class(
    "search.indexing.settings", "get_attributes_to_index"
)

CategoryElasticSearchRelatedResource = get_class(
    "search.mappings.products.resources", "CategoryElasticSearchRelatedResource"
)
ProductElasticSearchResource = get_class(
    "search.mappings.products.resources", "ProductElasticSearchResource"
)

ATTRIBUTES_TO_INDEX = get_attributes_to_index().keys()


class CategoryRelatedMapping(OscarBaseMapping):
    from_resource = CategoryResource
    to_resource = CategoryElasticSearchRelatedResource

    @odin.assign_field
    def description(self) -> str:
        return strip_tags(self.source.description)


class ProductMapping(OscarBaseMapping):
    from_resource = ProductResource
    to_resource = ProductElasticSearchResource

    register_mapping = False

    mappings = (
        odin.define(from_field="upc", to_field="code_auto_complete"),
        odin.define(from_field="upc", to_field="code"),
        odin.define(from_field="is_available_to_buy", to_field="is_available"),
    )

    @odin.assign_field
    def popularity(self):
        months_to_run = settings.MONTHS_TO_RUN_ANALYTICS
        orders_above_date = timezone.now() - relativedelta(months=months_to_run)

        return Line.objects.filter(
            product_id=self.source.id, order__date_placed__gte=orders_above_date
        ).count()

    @odin.assign_field
    def content_type(self) -> str:
        content_type = ContentType.objects.get_for_model(Product)
        return ".".join(content_type.natural_key())

    @odin.assign_field(to_list=True)
    def categories(self) -> str:
        return CategoryRelatedMapping.apply(self.source.categories)

    @odin.map_field(from_field="attributes")
    def attrs(self, attributes):
        attrs = {}
        for code in ATTRIBUTES_TO_INDEX:
            if code in attributes:
                attrs[code] = str(attributes[code])

        return attrs

    @odin.assign_field(to_list=True)
    def status(self):
        ctx = []

        if not self.source.is_public:
            return ["n"]

        ctx.append(ES_CTX_PUBLIC)

        # non public items are not available or browsable
        if self.source.is_available_to_buy:
            ctx.append(ES_CTX_AVAILABLE)

        # depending on FILTER_AVAILABLE things are browsable only if
        # they are available
        is_browsable = (
            self.source.structure == Product.STANDALONE
            or self.source.structure == Product.PARENT
        )
        if not settings.FILTER_AVAILABLE and is_browsable:
            ctx.append(ES_CTX_BROWSABLE)
        elif self.source.is_available_to_buy and is_browsable:
            ctx.append(ES_CTX_BROWSABLE)

        return ctx

    @odin.assign_field(to_list=True)
    def string_attrs(self):
        attrs = [str(a) for a in self.source.attributes.values()]
        if self.source.structure == Product.PARENT:
            for child in Product.objects.filter(parent_id=self.source.id):
                attrs.append(child.title)
                attrs.extend(
                    [str(a.value_as_text) for a in child.get_attribute_values()]
                )

        return attrs

    @odin.assign_field
    def facets(self) -> str:
        facets = {}
        attributes = self.source.attributes

        for definition in settings.FACETS:
            name = definition["name"].replace("facets.", "")
            if name in attributes.keys():
                facets[name] = attributes[name]

        return facets

    @odin.map_field(
        from_field=settings.AUTOCOMPLETE_SEARCH_FIELDS, to_field="suggest", to_list=True
    )
    def suggest(self, *args):
        return list(args)

    @odin.map_field(
        from_field="title", to_field=["title", "search_title", "title_auto_complete"]
    )
    def title(self, title):
        return title, title, title