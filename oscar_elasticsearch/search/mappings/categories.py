import odin

from django.utils.html import strip_tags

from oscar.core.loading import get_class, get_model

from oscar_odin.resources.catalogue import Category as CategoryResource

from django.contrib.contenttypes.models import ContentType

OscarElasticSearchResourceMixin = get_class(
    "search.mappings.mixins", "OscarElasticSearchResourceMixin"
)

Category = get_model("catalogue", "Category")


class CategoryElasticSearchResource(OscarElasticSearchResourceMixin):
    full_name: str
    full_slug: str
    _index: str


class CategoryMapping(odin.Mapping):
    from_resource = CategoryResource
    to_resource = CategoryElasticSearchResource

    @odin.assign_field
    def content_type(self) -> str:
        content_type = ContentType.objects.get_for_model(Category)
        return ".".join(content_type.natural_key())

    @odin.assign_field
    def title(self) -> str:
        return self.source.name

    @odin.assign_field
    def description(self) -> str:
        return strip_tags(self.source.description)

    @odin.assign_field
    def code(self) -> str:
        return "%s-%s" % (self.source.slug, self.source.id)

    @odin.assign_field
    def _index(self) -> str:
        return self.context.get("_index")


class ElasticSearchResource(odin.AnnotatedResource):
    _index: str
    _id: str
    _source: CategoryElasticSearchResource


class CategoryElasticSearchMapping(odin.Mapping):
    from_resource = CategoryResource
    to_resource = ElasticSearchResource

    mappings = (odin.define(from_field="id", to_field="_id"),)

    @odin.assign_field
    def _source(self) -> str:
        return CategoryMapping.apply(self.source)

    @odin.assign_field
    def _index(self) -> str:
        return self.context.get("_index")
