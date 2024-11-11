import odin

from oscar.core.loading import get_class

OscarResource = get_class("oscar_odin.resources.base", "OscarResource")
ProductResource = get_class("oscar_odin.resources.catalogue", "ProductResource")
CategoryResource = get_class("oscar_odin.resources.catalogue", "CategoryResource")

OscarBaseMapping = get_class("oscar_odin.mappings.common", "OscarBaseMapping")

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
        return ProductMapping.apply(self.source, self.context)

    @odin.assign_field
    def _index(self) -> str:
        return self.context.get("_index")
