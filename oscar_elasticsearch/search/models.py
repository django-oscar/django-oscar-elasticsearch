from django.utils import timezone
from django.conf import settings

from dateutil.relativedelta import relativedelta

from oscar.core.loading import is_model_registered, get_model, get_class

from wagtail.search import index

from .abstract_models import AbstractSynonym
from .utils import es_type_for_product_attribute, product_attributes_es_config, merge_dicts

process_product_fields = get_class("search.extra", "process_product_fields")

__all__ = []


if not is_model_registered("search", "Synonym"):

    class Synonym(AbstractSynonym):
        pass

    __all__.append("Synonym")


if is_model_registered("catalogue", "Product"):

    class ProductProxy(index.Indexed, get_model("catalogue", "Product")):
        def popularity(self):
            months_to_run = settings.OSCAR_SEARCH.get("MONTHS_TO_RUN_ANALYTICS", 3)
            orders_above_date = timezone.now() - relativedelta(months=months_to_run)

            Line = get_model("order", "Line")

            return Line.objects.filter(
                product=self, order__date_placed__gte=orders_above_date
            ).count()

        def price(self):
            selector = get_class("partner.strategy", "Selector")
            strategy = selector().strategy()
            if self.is_parent:
                return strategy.fetch_for_parent(self).price.incl_tax

            return strategy.fetch_for_product(self).price.incl_tax

        def string_attrs(self):
            return [str(a.value_as_text) for a in self.attribute_values.all()]

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

            return result

        def object(self):
            "Mimic a haystack search result"
            return self

        def category_id(self):
            return self.categories.values_list("id", flat=True)

        def category_name(self):
            return list(self.categories.values_list("name", flat=True))

        @classmethod
        def get_search_fields(cls):  # hook extra_product_fields for overriding
            return process_product_fields(super().get_search_fields())

        search_fields = [
            index.FilterField("id"),
            index.SearchField("title", partial_match=True, boost=2),
            index.AutocompleteField("title"),
            index.AutocompleteField("upc", es_extra={"analyzer": "keyword"}),
            index.FilterField("upc"),
            index.SearchField("upc", boost=3, es_extra={"analyzer": "keyword"}),
            index.SearchField("description", partial_match=True),
            index.FilterField("popularity"),
            index.FilterField("price", es_extra={"type": "double"}),
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
        ]

        class Meta:
            proxy = True

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

    __all__.append("CategoryProxy")
