import odin
from oscar_odin.mappings import catalogue
from oscar_odin.resources.catalogue import Product as ProductResource
from oscar_odin.resources._base import OscarResource

from oscar.core.loading import get_model

from django.contrib.contenttypes.models import ContentType

Product = get_model("catalogue", "Product")


class ProductElasticSearchResource(odin.AnnotatedResource):
    id: str
    content_type: str
    title: str
    is_public: bool
    upc: str
    description: str


class ElasticSearchResource(odin.AnnotatedResource):
    _index: str
    _type: str
    _id: str
    _source: ProductElasticSearchResource


class ProductMapping(odin.Mapping):
    from_resource = ProductResource
    to_resource = ProductElasticSearchResource

    @odin.assign_field
    def content_type(self) -> str:
        content_type = ContentType.objects.get_for_model(Product)
        return ".".join(content_type.natural_key())


class ProductElasticSearchMapping(odin.Mapping):
    from_resource = ProductResource
    to_resource = ElasticSearchResource

    mappings = (odin.define(from_field="id", to_field="_id"),)

    @odin.assign_field
    def _source(self) -> str:
        """Map title field."""
        return ProductMapping.apply(self.source)

    @odin.assign_field
    def _index(self) -> str:
        return self.context.get("_index")

    @odin.assign_field
    def _type(self) -> str:
        return self.context.get("_type")
