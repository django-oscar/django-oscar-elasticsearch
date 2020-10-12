from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from dateutil.relativedelta import relativedelta

from oscar.core.loading import is_model_registered, get_model, get_class, get_classes

from extendedsearch import index

from .constants import ES_CTX_PUBLIC, ES_CTX_AVAILABLE, ES_CTX_BROWSABLE
from . import settings

merge_dicts, es_type_for_product_attribute, product_attributes_es_config = get_classes(
    "search.utils",
    ["merge_dicts", "es_type_for_product_attribute", "product_attributes_es_config"],
)
process_product_fields = get_class("search.extra", "process_product_fields")
ProductProxyMixin = get_class("search.mixins", "ProductProxyMixin")


__all__ = []


if is_model_registered("catalogue", "Product"):

    class ProductProxy(get_model("catalogue", "Product"), ProductProxyMixin):
        def popularity(self):
            months_to_run = settings.MONTHS_TO_RUN_ANALYTICS
            orders_above_date = timezone.now() - relativedelta(months=months_to_run)

            Line = get_model("order", "Line")

            return Line.objects.filter(
                product=self, order__date_placed__gte=orders_above_date
            ).count()

        @cached_property
        def purchase_info(self):
            selector = get_class("partner.strategy", "Selector")
            strategy = selector().strategy()
            if self.is_parent:
                return strategy.fetch_for_parent(self)

            return strategy.fetch_for_product(self)

        def is_available(self):
            return self.purchase_info.availability.is_available_to_buy

        def price(self):
            purchase_info = self.purchase_info
            if purchase_info.price.exists:
                return purchase_info.price.incl_tax

            return None

        def status(self):
            ctx = []
            if self.is_public:
                ctx.append(ES_CTX_PUBLIC)

                # non public items are not available or browsable
                if self.is_available():
                    ctx.append(ES_CTX_AVAILABLE)

                # depending on FILTER_AVAILABLE things are browsable only if
                # they are available
                is_browsable = self.is_standalone or self.is_parent
                if not settings.FILTER_AVAILABLE and is_browsable:
                    ctx.append(ES_CTX_BROWSABLE)
                elif self.is_available() and is_browsable:
                    ctx.append(ES_CTX_BROWSABLE)

            return ctx

        def string_attrs(self):
            attrs = [str(a.value_as_text) for a in self.attribute_values.all()]
            if self.structure == self.PARENT:
                for child in ProductProxy.objects.filter(parent=self):
                    attrs.append(child.title)
                    attrs.extend(child.string_attrs())

            return attrs

        def child_upc(self):
            upcs = []
            if self.structure == self.PARENT:
                for child in ProductProxy.objects.filter(parent=self):
                    upcs.append(child.upc)
            return upcs

        def attrs(self):
            values = self.attribute_values.all().select_related("attribute")
            result = {}
            for value in values:
                at = value.attribute
                if at.type == at.OPTION:
                    result[value.attribute.code] = value.value.option
                elif at.type == at.MULTI_OPTION:
                    result[value.attribute.code] = [a.option for a in value.value]
                elif es_type_for_product_attribute(at) != "text":
                    result[value.attribute.code] = value.value

            if self.is_parent:
                for child in ProductProxy.objects.filter(parent=self):
                    result = merge_dicts(result, child.attrs())

            return self.process_attributes(result)

        def object(self):
            """Mimic a haystack search result"""
            return self

        def product_class__name(self):
            return self.get_product_class().name

        def category_id(self):
            return self.categories.values_list("id", flat=True)

        def category_name(self):
            return list(self.categories.values_list("name", flat=True))

        @classmethod
        def get_indexed_objects(cls):
            return cls.objects.all()

        @classmethod
        def get_search_fields(cls):  # hook extra_product_fields for overriding
            search_fields = super().get_search_fields()
            return process_product_fields(search_fields)

        @classmethod
        def get_autocomplete_contexts(cls):
            return settings.AUTOCOMPLETE_CONTEXTS

        @classmethod
        def get_facets(cls):
            return settings.FACETS

        # See oscar_elasticsearch.search.search.boosted_fields
        # for default boost values
        search_fields = [
            index.FilterField("id"),
            index.FilterField("product_class__name"),
            index.FilterField("title"),
            index.SearchField("title", partial_match=True),
            index.FilterField("is_public"),
            index.AutocompleteField("title"),
            index.AutocompleteField("upc", es_extra={"analyzer": "keyword"}),
            index.FilterField("upc"),
            index.SearchField("upc", es_extra={"analyzer": "keyword"}),
            index.SearchField("child_upc", es_extra={"analyzer": "keyword"}),
            index.AutocompleteField("child_upc", es_extra={"analyzer": "keyword"}),
            index.SearchField("description", partial_match=True),
            index.FilterField("popularity"),
            index.FilterField("price", es_extra={"type": "double"}),
            index.FilterField("is_available", es_extra={"type": "boolean"}),
            index.FilterField("category_id"),
            index.SearchField("category_name", partial_match=True),
            index.AutocompleteField("category_name"),
            index.RelatedFields(
                "categories",
                [
                    index.SearchField("description", partial_match=True),
                    index.SearchField("slug"),
                    index.SearchField("full_name"),
                    index.SearchField("get_absolute_url"),
                ],
            ),
            index.RelatedFields(
                "stockrecords",
                [
                    index.FilterField("price_currency"),
                    index.SearchField("partner_sku"),
                    index.SearchField("price_excl_tax"),
                    index.FilterField("partner"),
                    index.FilterField("num_in_stock"),
                ],
            ),
            index.FilterField("parent_id"),
            index.FilterField("structure"),
            index.FilterField("is_standalone"),
            index.FilterField("slug"),
            index.FilterField("rating"),
            index.FilterField("date_created"),
            index.FilterField("date_updated"),
            index.SearchField("string_attrs"),
            index.FilterField("attrs", es_extra=product_attributes_es_config()),
        ] + ProductProxyMixin.search_fields

        class Meta:
            proxy = True
            verbose_name = _("Product")
            verbose_name_plural = _("Products")
            managed = False
            app_label = "search"

    __all__.append("ProductProxy")


if is_model_registered("catalogue", "Category"):

    class CategoryProxy(index.Indexed, get_model("catalogue", "Category")):
        search_fields = [
            index.SearchField("name", partial_match=True, boost=2),
            index.AutocompleteField("name"),
            index.SearchField("description"),
            index.SearchField("full_name"),
            index.FilterField("full_slug"),
            index.FilterField("slug"),
            index.FilterField("get_absolute_url"),
        ]

        class Meta:
            proxy = True
            managed = False
            app_label = "search"

    __all__.append("CategoryProxy")
