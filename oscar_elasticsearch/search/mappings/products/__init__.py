import odin

from oscar.core.loading import get_class

from oscar_odin.resources._base import OscarResource
from oscar_odin.resources.catalogue import (
    Product as ProductResource,
    Category as CategoryResource,
)
from oscar_odin.mappings._common import OscarBaseMapping

ProductElasticSearchResource = get_class(
    "search.mappings.products.resources", "ProductElasticSearchResource"
)
ProductMapping = get_class("search.mappings.products.mappings", "ProductMapping")


class ElasticSearchResource(OscarResource):
    _index: str
    _id: str
    _source: ProductElasticSearchResource
    _op_type: str = "index"


class ProductElasticSearchMapping(OscarBaseMapping):
    from_resource = ProductResource
    to_resource = ElasticSearchResource

    register_mapping = False

    mappings = (odin.define(from_field="id", to_field="_id"),)

    @odin.assign_field
    def _source(self) -> str:
        return ProductMapping.apply(self.source)

    @odin.assign_field
    def _index(self) -> str:
        return self.context.get("_index")
