import operator

from django.views.generic.list import ListView
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

from oscar.core.loading import get_class, get_model

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

    def get_elasticsearch_body(self):
        return {"query": {"match_all": {}}}

    def get_search_results(self):
        elasticsearch_from = (
            int(self.request.GET.get("page", 1)) * self.paginate_by
        ) - self.paginate_by

        print(self.get_elasticsearch_body())
        return es.search(
            index=OSCAR_PRODUCTS_INDEX_NAME,
            body=self.get_elasticsearch_body(),
            size=self.paginate_by,
            from_=elasticsearch_from,
        )

    def paginate(self, results, products):
        total_hits = results["hits"]["total"]

        return ElasticSearchPaginator(
            range(0, total_hits), self.paginate_by, products=products
        )

    def get_context_data(self, *args, **kwargs):
        # context = super().get_context_data(*args, **kwargs)
        context = {}
        search_results = self.get_search_results()

        idgetter = operator.itemgetter("id")
        product_ids = [
            idgetter(hit["_source"]) for hit in search_results["hits"]["hits"]
        ]

        products = Product.objects.filter(pk__in=product_ids)
        paginator = self.paginate(search_results, products)

        context["paginator"] = paginator
        page_obj = paginator.get_page(self.request.GET.get("page", 1))
        context["page_obj"] = page_obj
        #         context["suggestion"] = suggestion
        context["page"] = page_obj
        context[self.context_object_name] = page_obj
        #         context["facet_data"] = LegacyOscarFacetList(processed_facets)
        #         context["has_facets"] = bool(processed_facets)
        #         context["query"] = self.form.cleaned_data.get("q") or gettext("Blank")
        #         context["form"] = self.form
        return context
