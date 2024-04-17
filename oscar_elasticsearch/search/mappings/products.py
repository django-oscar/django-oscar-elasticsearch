import odin

from typing import Optional, List

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.html import strip_tags

from dateutil.relativedelta import relativedelta
from datetime import datetime

from decimal import Decimal

from oscar.core.loading import get_model, get_class

from oscar_odin.mappings._common import OscarBaseMapping
from oscar_odin.resources._base import OscarResource
from oscar_odin.mappings import catalogue
from oscar_odin.fields import DecimalField
from oscar_odin.resources.catalogue import (
    Product as ProductResource,
    Category as CategoryResource,
)
from oscar_odin.resources._base import OscarResource


from oscar_elasticsearch.search import settings

Product = get_model("catalogue", "Product")
Line = get_model("order", "Line")

OscarElasticSearchResourceMixin = get_class(
    "search.mappings.mixins", "OscarElasticSearchResourceMixin"
)
get_attributes_to_index = get_class(
    "search.indexing.settings", "get_attributes_to_index"
)

__all__ = [
    "ProductElasticSearchResource",
    "ElasticSearchResource",
    "ProductMapping",
    "ProductElasticSearchMapping",
]


ATTRIBUTES_TO_INDEX = get_attributes_to_index().keys()


class CategoryElasticSearchRelatedResource(OscarResource):
    id: int
    description: str
    full_name: str


class CategoryRelatedMapping(OscarBaseMapping):
    from_resource = CategoryResource
    to_resource = CategoryElasticSearchRelatedResource

    @odin.assign_field
    def description(self) -> str:
        return strip_tags(self.source.description)


class ProductElasticSearchResource(OscarElasticSearchResourceMixin):
    search_title: str
    autocomplete_title: str
    structure: str
    rating: Optional[float]
    priority: int
    parent_id: Optional[int]
    price: Decimal = DecimalField()
    currency: str
    num_available: int
    is_available: bool
    categories: List[CategoryElasticSearchRelatedResource]
    attrs: dict
    date_created: datetime
    date_updated: datetime
    string_attrs: List[str]
    facets: dict
    popularity: int


class ElasticSearchResource(OscarResource):
    _index: str
    _id: str
    _source: ProductElasticSearchResource
    _op_type: str = "index"


class ProductMapping(OscarBaseMapping):
    from_resource = ProductResource
    to_resource = ProductElasticSearchResource

    mappings = (
        odin.define(from_field="upc", to_field="code"),
        odin.define(from_field="is_available_to_buy", to_field="is_available"),
    )

    @odin.assign_field
    def popularity(self):
        months_to_run = settings.MONTHS_TO_RUN_ANALYTICS
        orders_above_date = timezone.now() - relativedelta(months=months_to_run)

        popularity = Line.objects.filter(
            product_id=self.source.id, order__date_placed__gte=orders_above_date
        ).count()

        print(self.source.upc, popularity)
        return popularity

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
        from_field="title", to_field=["title", "search_title", "autocomplete_title"]
    )
    def title(self, title):
        return title, title, title


class ProductElasticSearchMapping(OscarBaseMapping):
    from_resource = ProductResource
    to_resource = ElasticSearchResource

    mappings = (odin.define(from_field="id", to_field="_id"),)

    @odin.assign_field
    def _source(self) -> str:
        return ProductMapping.apply(self.source)

    @odin.assign_field
    def _index(self) -> str:
        return self.context.get("_index")
