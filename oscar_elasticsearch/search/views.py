# pylint: disable=not-callable
from django.contrib import messages
from django.core.paginator import InvalidPage
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from oscar.core.loading import get_class

from purl import URL

get_product_search_handler_class = get_class(
    "catalogue.search_handlers", "get_product_search_handler_class"
)
ProductAutocompleteHandler = get_class(
    "search.search_handlers", "ProductAutocompleteHandler"
)
SearchForm = get_class("search.forms", "SearchForm")
user_search = get_class("search.signals", "user_search")


class BaseSearchView(TemplateView):
    search_handler_class = None
    search_signal = None

    def get_search_handler(self):
        return self.search_handler_class(self.request.GET, self.request.get_full_path())

    def get(self, request, *args, **kwargs):
        try:
            search_handler = self.get_search_handler()
            if not search_handler.is_valid():
                for error_list in search_handler.form.errors.values():
                    for msg in error_list:
                        messages.error(request, msg)

            self.extra_context = search_handler.context
        except InvalidPage:
            messages.error(request, _("The given page number was invalid."))
            return HttpResponseRedirect(self.remove_page_arg(request.get_full_path()))

        # Raise a signal for other apps to hook into for analytics
        self.search_signal.send(
            sender=self,
            session=request.session,
            user=request.user,
            query=search_handler.form.cleaned_data.get("q"),
        )

        return super().get(request, *args, **kwargs)

    @staticmethod
    def remove_page_arg(url):
        url = URL(url)
        return url.remove_query_param("page").as_string()


class BaseAutoCompleteView(View):

    form_class = None
    query_class = None

    def get_query(self, form):
        return self.query_class(**self.get_query_kwargs(form))

    def get_query_kwargs(self, form):
        kwargs = {"query": form.cleaned_data["q"]}
        return kwargs

    def search(self):
        form = self.form_class(self.request.GET)
        if form.is_valid():
            s = self.get_query(form)
            results = s.get_suggestions()
            return results
        else:
            return []

    def get(self, request, *args, **kwargs):
        results = self.search()
        if results:
            return JsonResponse(results, safe=False)
        else:
            return JsonResponse(results, safe=False, status=400)


class CatalogueSearchView(BaseSearchView):
    template_name = "search/results.html"
    search_signal = user_search
    search_handler_class = get_product_search_handler_class()


class CatalogueAutoCompleteView(BaseAutoCompleteView):
    form_class = SearchForm
    query_class = ProductAutocompleteHandler
