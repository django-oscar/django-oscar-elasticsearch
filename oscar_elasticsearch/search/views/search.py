from django.utils.translation import gettext_lazy as _
from django.views import View
from django.http import JsonResponse

from oscar.core.loading import get_class

from oscar_elasticsearch.search.indexing.settings import OSCAR_PRODUCTS_INDEX_NAME
from oscar_elasticsearch.search.settings import (
    SUGGESTION_STATUS_FILTER,
)

es = get_class("search.backend", "es")
autocomplete_suggestions = get_class(
    "search.api.autocomplete", "autocomplete_suggestions"
)


class CatalogueAutoCompleteView(View):
    def get_suggestion_context(self):
        return {"status": SUGGESTION_STATUS_FILTER}

    def get_suggestions(self):
        search_string = self.request.GET.get("q", "")

        return autocomplete_suggestions(
            OSCAR_PRODUCTS_INDEX_NAME,
            search_string,
            "suggest",
            skip_duplicates=True,
            contexts=self.get_suggestion_context(),
        )

    # pylint: disable=W0613
    def get(self, request, *args, **kwargs):
        results = self.get_suggestions()
        if results:
            return JsonResponse(results, safe=False)
        else:
            return JsonResponse(results, safe=False, status=400)
