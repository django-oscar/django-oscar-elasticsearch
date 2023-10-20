import logging

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.utils.translation import gettext

from oscar.core.loading import get_model, get_class

from extendedsearch.backends import get_search_backend
from extendedsearch.utils import separate_filters_from_query
from extendedsearch.query import MatchAll

from elasticsearch.exceptions import RequestError

from . import settings
from .utils import LegacyOscarFacetList

logger = logging.getLogger(__name__)

SearchBackend = get_search_backend()

ProductProxy = get_model("search", "ProductProxy")

CatalogueSearchForm = get_class("search.forms", "CatalogueSearchForm")
process_facets = get_class("search.facets", "process_facets")
get_facet_names = get_class("search.utils", "get_facet_names")
select_suggestion = get_class("search.suggestions", "select_suggestion")
query_hit = get_class("search.signals", "query_hit")


class ElasticSearchViewMixin:
    model = ProductProxy
    paginate_by = settings.DEFAULT_ITEMS_PER_PAGE
    form_class = CatalogueSearchForm

    order_by_relevance = True
    facets = get_facet_names()
    suggestion_field_name = "title"

    def build_form(self, **kwargs):
        kwargs["selected_facets"] = self.request.GET.getlist("selected_facets")
        return self.form_class(self.request.GET, **kwargs)

    def get_base_search_results(self, query, queryset, order_by_relevance):
        results = SearchBackend.search(
            query, queryset, order_by_relevance=order_by_relevance
        )

        if settings.FILTER_AVAILABLE:
            results = results.es_filter(is_available=True)

        return results

    def get_es_ordering(self):
        ordering = self.form.get_sort_params(self.form.cleaned_data)
        if ordering:
            return [ordering]
        return []

    def get_query(self):
        filters, query_string = separate_filters_from_query(
            self.form.cleaned_data.get("q")
        )
        if not query_string or query_string == "*":
            return filters, MatchAll()
        else:
            query_hit.send(sender=self, querystring=query_string)

        return filters, query_string

    def get_queryset(self):
        return self.model.objects.browsable()

    def get_results(self, order_by_relevance=True):
        """
        Fetches the results via the form.
        """
        if not self.form.is_valid():
            logger.error("Invalid form %s", self.form.errors)
            return self.get_base_search_results(
                MatchAll(),
                self.get_queryset().filter(
                    pk__isnull=True
                ),  # queryset.none() can not be handled by the elasticsearch querycompiler
                order_by_relevance=order_by_relevance,
            )

        filters, query = self.get_query()
        filters.update(self.form.selected_multi_facets)

        return (
            self.get_base_search_results(
                query, self.get_queryset(), order_by_relevance=order_by_relevance
            )
            .es_filter(**filters)
            .es_order_by(self.get_es_ordering())
        )

    def paginate(self, search_results):
        page = self.request.GET.get("page", 1)
        paginator = Paginator(
            search_results,
            self.form.cleaned_data.get("items_per_page", self.paginate_by),
        )

        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        return page_obj, paginator

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        self.form = self.build_form()

        search_results = self.get_results(order_by_relevance=self.order_by_relevance)

        try:
            if search_results.count():  # there are actual search results
                page_obj, paginator = self.paginate(search_results)
                facets = page_obj.object_list.facets(*self.facets)
                processed_facets = process_facets(
                    self.request.get_full_path(), self.form, facets
                )
                suggestion = None
            else:  # no results, fetch suggestions
                page_obj, paginator = self.paginate(self.get_queryset().none())
                facets = search_results.facets(*self.facets)
                processed_facets = process_facets(
                    self.request.get_full_path(), self.form, facets
                )
                suggestions = search_results.suggestions(self.suggestion_field_name)
                suggestion = select_suggestion(self.suggestion_field_name, suggestions)
        except RequestError as e:
            logger.exception(e)
            page_obj, paginator = self.paginate(self.get_queryset().none())
            facets = []
            processed_facets = []
            suggestion = None

        context["paginator"] = paginator
        context["page_obj"] = page_obj
        context["suggestion"] = suggestion
        context["page"] = page_obj
        context[self.context_object_name] = page_obj
        context["facet_data"] = LegacyOscarFacetList(processed_facets)
        context["has_facets"] = bool(processed_facets)
        context["query"] = self.form.cleaned_data.get("q") or gettext("Blank")
        context["form"] = self.form
        return context
