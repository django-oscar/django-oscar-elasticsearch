from decimal import Decimal as D

from django.views.generic.list import ListView
from django.utils.translation import gettext

from oscar.core.loading import get_class, get_model

from oscar_elasticsearch.search import settings
from oscar_elasticsearch.search.facets import process_facets
from oscar_elasticsearch.search.signals import query_hit

OSCAR_PRODUCTS_INDEX_NAME = get_class(
    "search.indexing.settings", "OSCAR_PRODUCTS_INDEX_NAME"
)
select_suggestion = get_class("search.suggestions", "select_suggestion")
es = get_class("search.backend", "es")
ProductElasticsearchIndex = get_class("search.api.product", "ProductElasticsearchIndex")

Product = get_model("catalogue", "Product")


product_search_api = ProductElasticsearchIndex()


class BaseSearchView(ListView):
    model = Product
    paginate_by = settings.DEFAULT_ITEMS_PER_PAGE
    form_class = None
    aggs_definitions = settings.FACETS
    scoring_functions = [
        {
            "field_value_factor": {
                "field": "priority",
                "modifier": "ln2p",
                "factor": 1,
                "missing": 0,
            },
        },
    ]

    def get_aggs_definitions(self):
        return self.aggs_definitions

    def get_scoring_functions(self):
        return self.scoring_functions if self.scoring_functions else None

    def get_default_filters(self):
        filters = [{"term": {"is_public": True}}]

        if settings.FILTER_AVAILABLE:
            filters.append({"term": {"is_available": True}})

        return filters

    def get_facet_filters(self):
        filters = []

        for name, value in self.form.selected_multi_facets.items():
            # pylint: disable=W0640
            definition = list(
                filter(lambda x: x["name"] == name, self.get_aggs_definitions())
            )[0]
            if definition["type"] == "range":
                ranges = []
                for val in value:
                    if val.startswith("*-"):
                        ranges.append(
                            {"range": {name: {"to": D(val.replace("*-", ""))}}}
                        )
                    elif val.endswith("-*"):
                        ranges.append(
                            {"range": {name: {"from": D(val.replace("-*", ""))}}}
                        )
                    else:
                        from_, to = val.split("-")
                        ranges.append(
                            {"range": {name: {"from": D(from_), "to": D(to)}}}
                        )

                filters.append({"bool": {"should": ranges}})
            else:
                filters.append({"terms": {name: value}})

        return filters

    def get_sort_by(self):
        sort_by = []
        ordering = self.form.get_sort_params(self.form.cleaned_data)

        if not ordering and not self.request.GET.get("q"):
            ordering = settings.DEFAULT_ORDERING

        if ordering:
            if ordering.startswith("-"):
                sort_by.insert(0, {"%s" % ordering.replace("-", ""): {"order": "desc"}})
            else:
                sort_by.insert(0, {"%s" % ordering: {"order": "asc"}})

        else:
            sort_by.append("_score")

        return sort_by

    def get_form(self, request):
        # pylint: disable=E1102
        return self.form_class(
            data=request.GET or {},
            selected_facets=request.GET.getlist("selected_facets", []),
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # pylint: disable=W0201
        self.form = self.get_form(self.request)
        self.form.is_valid()

        elasticsearch_from = (
            int(self.request.GET.get("page", 1)) * self.paginate_by
        ) - self.paginate_by

        query_string = self.request.GET.get("q", "")
        if query_string:
            query_hit.send(sender=self, querystring=query_string)

        paginator, search_results, unfiltered_result = (
            product_search_api.paginated_facet_search(
                from_=elasticsearch_from,
                query_string=query_string,
                filters=self.get_default_filters(),
                sort_by=self.get_sort_by(),
                scoring_functions=self.get_scoring_functions(),
                facet_filters=self.get_facet_filters(),
                aggs_definitions=self.get_aggs_definitions(),
            )
        )

        if "aggregations" in unfiltered_result:
            processed_facets = process_facets(
                self.request.get_full_path(),
                self.form,
                (unfiltered_result, search_results),
                facet_definitions=self.get_aggs_definitions(),
            )
        else:
            processed_facets = None

        context["paginator"] = paginator
        page_obj = paginator.get_page(self.request.GET.get("page", 1))
        context["page_obj"] = page_obj
        context["suggestion"] = select_suggestion(
            product_search_api.get_suggestion_field_name(None),
            search_results.get("suggest", []),
        )
        context["page"] = page_obj
        context[self.context_object_name] = page_obj
        context["facet_data"] = processed_facets
        context["has_facets"] = bool(processed_facets)
        context["query"] = self.request.GET.get("q") or gettext("Blank")
        context["form"] = self.form

        return context
