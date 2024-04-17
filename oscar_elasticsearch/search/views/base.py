import operator

from decimal import Decimal as D

from django.views.generic.list import ListView
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.utils.translation import gettext

from oscar.core.loading import get_class, get_model

from oscar_elasticsearch.exceptions import ElasticSearchQueryException
from oscar_elasticsearch.search import settings
from oscar_elasticsearch.search.facets import process_facets
from oscar_elasticsearch.search.utils import LegacyOscarFacetList
from oscar_elasticsearch.search.settings import FILTER_AVAILABLE

DEFAULT_ITEMS_PER_PAGE = get_class("search.settings", "DEFAULT_ITEMS_PER_PAGE")

OSCAR_PRODUCTS_INDEX_NAME = get_class(
    "search.indexing.settings", "OSCAR_PRODUCTS_INDEX_NAME"
)
select_suggestion = get_class("search.suggestions", "select_suggestion")
es = get_class("search.backend", "es")

Product = get_model("catalogue", "Product")


class ElasticSearchPaginator(Paginator):
    def __init__(self, *args, **kwargs):
        self.products = kwargs.pop("products")
        super().__init__(*args, **kwargs)

    def page(self, number):
        """Return a Page object for the given 1-based page number."""
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        return self._get_page(self.products, number, self)


class BaseSearchView(ListView):
    model = Product
    paginate_by = DEFAULT_ITEMS_PER_PAGE
    suggestion_field_name = "search_title"

    def get_elasticsearch_aggs(self):
        aggs = {}

        for facet_definition in settings.FACETS:
            name = facet_definition["name"]
            facet_type = facet_definition["type"]
            if facet_type == "term":
                terms = {"terms": {"field": name}}

                if "order" in facet_definition:
                    terms["terms"]["order"] = {"_key": facet_definition["order"]}

                aggs[name] = terms
            elif facet_type == "range":
                ranges_definition = facet_definition["ranges"]
                ranges = [
                    (
                        {"to": ranges_definition[i]}
                        if i == 0
                        else {
                            "from": ranges_definition[i - 1],
                            "to": ranges_definition[i],
                        }
                    )
                    for i in range(len(ranges_definition))
                ]

                ranges.append({"from": ranges_definition[-1]})

                aggs[name] = {"range": {"field": name, "ranges": ranges}}

        return aggs

    def get_search_query(self):
        search_query = self.request.GET.get("q")

        if search_query:
            return [
                {
                    "query_string": {
                        "query": search_query,
                        "fields": settings.SEARCH_FIELDS,
                    }
                }
            ]

        else:
            return {"match_all": {}}

    def get_elasticsearch_filters(self, include_facets=True):
        filters = [{"term": {"is_public": True}}]

        if include_facets:

            for name, value in self.form.selected_multi_facets.items():
                definition = list(filter(lambda x: x["name"] == name, settings.FACETS))[
                    0
                ]
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
                            _from, to = val.split("-")
                            ranges.append(
                                {"range": {name: {"from": D(_from), "to": D(to)}}}
                            )

                    filters.append({"bool": {"should": ranges}})
                else:
                    filters.append({"terms": {name: value}})

        if FILTER_AVAILABLE:
            filters.append({"term": {"is_available": True}})

        return filters

    def get_sort_by(self):
        sort_by = []
        ordering = self.form.get_sort_params(self.form.cleaned_data)

        if ordering:
            if ordering.startswith("-"):
                sort_by.insert(0, {"%s" % ordering.replace("-", ""): {"order": "desc"}})
            else:
                sort_by.insert(0, {"%s" % ordering: {"order": "asc"}})

        else:
            sort_by.append("_score")

        return sort_by

    def get_elasticsearch_body(self, include_facets=True):
        return {
            "query": {
                "bool": {
                    "must": self.get_search_query(),
                    "filter": self.get_elasticsearch_filters(
                        include_facets=include_facets
                    ),
                }
            },
            "sort": self.get_sort_by(),
            "aggs": self.get_elasticsearch_aggs(),
            "suggest": {
                self.suggestion_field_name: {
                    "prefix": self.request.GET.get("q", ""),
                    "term": {"field": self.suggestion_field_name},
                }
            },
        }

    def get_search_results(self):
        elasticsearch_from = (
            int(self.request.GET.get("page", 1)) * self.paginate_by
        ) - self.paginate_by

        index_body = {"index": OSCAR_PRODUCTS_INDEX_NAME}

        result_body = self.get_elasticsearch_body()
        result_body["size"] = self.paginate_by
        result_body["from"] = elasticsearch_from

        unfiltered_body = self.get_elasticsearch_body(include_facets=False)
        unfiltered_body["size"] = 0

        multi_body = [
            index_body,
            result_body,
            index_body,
            unfiltered_body,
        ]

        return es.msearch(body=multi_body)["responses"]

    def paginate(self, search_results):
        status = search_results["status"]

        if status > 200:
            raise ElasticSearchQueryException(
                "Something went wrong during elasticsearch query", search_results
            )

        idgetter = operator.itemgetter("id")
        product_ids = [
            idgetter(hit["_source"]) for hit in search_results["hits"]["hits"]
        ]

        clauses = " ".join(
            ["WHEN id=%s THEN %s" % (pk, i) for i, pk in enumerate(product_ids)]
        )
        ordering = "CASE %s END" % clauses
        products = Product.objects.filter(pk__in=product_ids).extra(
            select={"ordering": ordering}, order_by=("ordering",)
        )

        total_hits = search_results["hits"]["total"]["value"]

        return ElasticSearchPaginator(
            range(0, total_hits), self.paginate_by, products=products
        )

    def get_form(self, request):
        return self.form_class(
            data=request.GET or {},
            selected_facets=request.GET.getlist("selected_facets", []),
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        self.form = self.get_form(self.request)
        self.form.is_valid()
        search_results, unfiltered_result = self.get_search_results()

        paginator = self.paginate(search_results)

        processed_facets = process_facets(
            self.request.get_full_path(),
            self.form,
            (unfiltered_result, search_results),
        )

        context["paginator"] = paginator
        page_obj = paginator.get_page(self.request.GET.get("page", 1))
        context["page_obj"] = page_obj
        context["suggestion"] = select_suggestion(
            self.suggestion_field_name, search_results["suggest"]
        )
        context["page"] = page_obj
        context[self.context_object_name] = page_obj
        context["facet_data"] = LegacyOscarFacetList(processed_facets)
        context["has_facets"] = bool(processed_facets)
        context["query"] = self.request.GET.get("q") or gettext("Blank")
        context["form"] = self.form

        return context
