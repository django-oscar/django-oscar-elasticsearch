import odin

from django.utils.html import strip_tags

from oscar.core.loading import get_class, get_model

OscarResource = get_class("oscar_odin.resources.base", "OscarResource")
CategoryResource = get_class("oscar_odin.resources.catalogue", "CategoryResource")

OscarBaseMapping = get_class("oscar_odin.mappings.common", "OscarBaseMapping")

OscarElasticSearchResourceMixin = get_class(
    "search.mappings.mixins", "OscarElasticSearchResourceMixin"
)

Category = get_model("catalogue", "Category")


class CategoryElasticSearchResource(OscarElasticSearchResourceMixin):
    full_name: str
    full_slug: str


class CategoryMapping(OscarBaseMapping):
    from_resource = CategoryResource
    to_resource = CategoryElasticSearchResource

    @odin.assign_field
    def content_type(self) -> str:
        return "catalogue.category"

    @odin.map_field(from_field="name", to_field=["title", "search_title"])
    def title(self, name) -> str:
        return name, name

    @odin.assign_field
    def description(self) -> str:
        return strip_tags(self.source.description)

    @odin.assign_field
    def code(self) -> str:
        if self.source.code:
            return self.source.code

        return "%s-%s" % (self.source.slug, self.source.id)


class ElasticSearchResource(OscarResource):
    _index: str
    _id: str
    _source: CategoryElasticSearchResource


class CategoryElasticSearchMapping(OscarBaseMapping):
    from_resource = CategoryResource
    to_resource = ElasticSearchResource

    mappings = (odin.define(from_field="id", to_field="_id"),)

    @odin.assign_field
    def _source(self) -> str:
        return CategoryMapping.apply(self.source)

    @odin.assign_field
    def _index(self) -> str:
        return self.context.get("_index")
