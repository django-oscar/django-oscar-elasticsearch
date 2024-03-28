import operator

from django.views.generic.list import ListView
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.utils.translation import gettext

from oscar.core.loading import get_class, get_model

from oscar_elasticsearch.search import settings
from oscar_elasticsearch.search.facets import process_facets
from oscar_elasticsearch.search.utils import LegacyOscarFacetList

DEFAULT_ITEMS_PER_PAGE = get_class("search.settings", "DEFAULT_ITEMS_PER_PAGE")
OSCAR_PRODUCTS_INDEX_NAME = get_class("search.settings", "OSCAR_PRODUCTS_INDEX_NAME")
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

    def get_aggs(self):
        return {
            facet_definition["name"]: {"terms": {"field": facet_definition["name"]}}
            for facet_definition in settings.FACETS
        }

    def get_elasticsearch_body(self, selected_facets={}):
        body = {"query": {"bool": {"must": {"match_all": {}}, "filter": []}}}

        for name, value in selected_facets.items():
            body["query"]["bool"]["filter"].append({"terms": {name: value}})

        return body

    def get_search_results(self):
        selected_facets = self.form.selected_multi_facets

        elasticsearch_from = (
            int(self.request.GET.get("page", 1)) * self.paginate_by
        ) - self.paginate_by

        index_body = {"index": OSCAR_PRODUCTS_INDEX_NAME}

        aggs = self.get_aggs()

        result_body = self.get_elasticsearch_body(selected_facets=selected_facets)
        result_body["size"] = self.paginate_by
        result_body["from"] = elasticsearch_from
        result_body["aggs"] = aggs

        unfiltered_body = self.get_elasticsearch_body()
        unfiltered_body["aggs"] = aggs
        unfiltered_body["size"] = 0

        multi_body = [
            index_body,
            result_body,
            index_body,
            unfiltered_body,
        ]

        return es.msearch(body=multi_body)["responses"]

    def paginate(self, search_results):
        idgetter = operator.itemgetter("id")
        product_ids = [
            idgetter(hit["_source"]) for hit in search_results["hits"]["hits"]
        ]
        products = Product.objects.filter(pk__in=product_ids)

        total_hits = search_results["hits"]["total"]["value"]

        return ElasticSearchPaginator(
            range(0, total_hits), self.paginate_by, products=products
        )

    def get_form(self, request):
        return self.form_class(
            selected_facets=request.GET.getlist("selected_facets", [])
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        self.form = self.get_form(self.request)
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
        #         context["suggestion"] = suggestion
        context["page"] = page_obj
        context[self.context_object_name] = page_obj
        context["facet_data"] = LegacyOscarFacetList(processed_facets)
        context["has_facets"] = bool(processed_facets)
        context["query"] = self.request.GET.get("q") or gettext("Blank")
        context["form"] = self.form

        return context
