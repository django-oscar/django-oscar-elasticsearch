from django.utils.translation import gettext_lazy as _
from django.views.generic.list import ListView
from django.views import View
from django.http import JsonResponse

from oscar.core.loading import get_model, get_class

from extendedsearch.backends import get_search_backend

SearchBackend = get_search_backend()

Category = get_model("catalogue", "Category")
ProductProxy = get_model("search", "ProductProxy")

unique_everseen = get_class("search.utils", "unique_everseen")


class CatalogueAutoCompleteView(View):
    model = ProductProxy
    search_fields = ["title", "upc", "categogry_name"]

    def get_queryset(self):
        return self.model.objects.browsable()

    def _search_suggestions(self):
        return SearchBackend.search_suggestions(
            self.request.GET.get("q"), self.get_queryset(), self.search_fields
        )

    def _get_suggestions(self):
        results = self._search_suggestions()
        for _, suggestions in results.items():
            for suggestion in suggestions:
                for opt in suggestion["options"]:
                    yield opt["text"]

    def get_suggestions(self):
        return list(unique_everseen(self._get_suggestions()))

    # pylint: disable=W0613
    def get(self, request, *args, **kwargs):
        results = self.get_suggestions()
        if results:
            return JsonResponse(results, safe=False)
        else:
            return JsonResponse(results, safe=False, status=400)
