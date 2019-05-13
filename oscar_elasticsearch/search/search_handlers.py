import logging
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.conf import settings
from django.utils.translation import gettext

from oscar.core.loading import get_model, get_class

from wagtail.search.backends import get_search_backend
from wagtail.search.utils import separate_filters_from_query
from wagtail.search.query import MatchAll
from wagtail.search.models import Query

from .utils import unique_everseen

SearchBackend = get_search_backend()

logger = logging.getLogger(__name__)

BaseSearchForm = get_class("search.forms", "BaseSearchForm")
CatalogueSearchForm = get_class("search.forms", "CatalogueSearchForm")
process_facets = get_class("search.facets", "process_facets")
get_facet_names = get_class("search.utils", "get_facet_names")
select_suggestion = get_class("search.suggestions", "select_suggestion")


class LegacyOscarFacetList(list):
    def items(self):
        for item in self:
            yield None, item


class SearchHandler(object):
    model = None
    form_class = BaseSearchForm

    def __init__(self, request_data, full_path, facets=None):
        self.full_path = full_path
        self.request_data = request_data
        self.form = self.build_form()
        self.facets = facets if facets is not None else get_facet_names()

        # Triggers the search. All exceptions (404, Invalid Page) must be raised
        # at init time from inside one of these methods.
        self.results = self.get_results()
        self.context = self.prepare_context(self.results)

    def get_search_context_data(self, context_object_name=None):
        if context_object_name:
            self.context[context_object_name] = self.context["page_obj"].object_list
        return self.context

    def build_form(self, **kwargs):
        kwargs["selected_facets"] = self.request_data.getlist("selected_facets")
        return self.form_class(self.request_data, **kwargs)

    def get_query(self):
        filters, query_string = separate_filters_from_query(
            self.form.cleaned_data.get("q")
        )
        if not query_string or query_string == "*":
            return filters, MatchAll()
        else:
            query_recorder = Query.get(query_string)
            query_recorder.add_hit()

        return filters, query_string

    def is_valid(self):
        return self.form.is_valid()

    def get_ordering(self):
        ordering = self.form.get_sort_params(self.form.cleaned_data)
        if ordering:
            return [ordering]
        return []

    def get_queryset(self):
        return self.model._default_manager.all()  # pylint: disable=protected-access

    def get_results(self):
        """
        Fetches the results via the form.
        """
        if not self.form.is_valid():
            logger.info("Invalid form")
            return self.get_queryset().none()

        filters, query = self.get_query()
        filters.update(self.form.selected_multi_facets)

        return (
            SearchBackend.search(query, self.get_queryset())
            .es_filter(**filters)
            .es_order_by(self.get_ordering())
        )

    def paginate(self, search_results):
        page = self.request_data.get("page", 1)
        paginator = Paginator(
            search_results, settings.OSCAR_SEARCH["DEFAULT_ITEMS_PER_PAGE"]
        )

        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        return page_obj, paginator

    def prepare_context(self, search_results):
        if search_results.count():  # there are actual search results
            page_obj, paginator = self.paginate(search_results)
            facets = page_obj.object_list.facets(*self.facets)
            processed_facets = process_facets(self.full_path, self.form, facets)
            suggestion = None
        else:  # no results, fetch suggestions
            page_obj, paginator = self.paginate(self.get_queryset().none())
            facets = search_results.facets(*self.facets)
            processed_facets = process_facets(self.full_path, self.form, facets)
            suggestions = search_results.suggestions("title")
            suggestion = select_suggestion("title", suggestions)

        return {
            "paginator": paginator,
            "page_obj": page_obj,
            "suggestion": suggestion,
            "page": page_obj,
            "facet_data": LegacyOscarFacetList(processed_facets),
            "has_facets": bool(processed_facets),
            "query": self.form.cleaned_data.get("q") or gettext("Blank"),
            "search_form": self.form,
        }


class AutocompleteHandler(object):
    model = get_model("search", "ProductProxy")

    def get_queryset(self):
        return self.model._default_manager.all()  # pylint: disable=protected-access

    def __init__(self, query=None):
        self.query = query

    def _search_suggestions(self):
        results = SearchBackend.search_suggestions(
            self.query, self.get_queryset(), ["title", "upc", "category_name"]
        )

        for _, suggestions in results.items():
            for suggestion in suggestions:
                for opt in suggestion["options"]:
                    yield opt["text"]

    def get_suggestions(self):
        return list(unique_everseen(self._search_suggestions()))


class ProductSearchHandler(SearchHandler):
    model = get_model("search", "ProductProxy")
    form_class = CatalogueSearchForm

    def __init__(self, request_data, full_path, categories=None, facets=None):
        self.categories = categories
        super().__init__(request_data, full_path, facets=facets)

    def get_queryset(self):
        qs = self.model.browsable.all()
        if self.categories:
            # no need to add distinct here as is being done in the base class.
            qs = qs.filter(categories__in=self.categories)
        return qs


class ProductAutocompleteHandler(AutocompleteHandler):
    pass
