from django.utils.translation import gettext_lazy as _
from django.views import View
from django.http import JsonResponse

from oscar.core.loading import get_model, get_class

from oscar_elasticsearch.search.indexing.settings import OSCAR_PRODUCTS_INDEX_NAME
from oscar_elasticsearch.search.settings import (
    NUM_SUGGESTIONS,
    SUGGESTION_STATUS_FILTER,
)

es = get_class("search.backend", "es")


class CatalogueAutoCompleteView(View):
    def get_suggestion_context(self):
        return {"status": SUGGESTION_STATUS_FILTER}

    def get_suggestions(self):
        body = {
            "suggest": {
                "autocompletion": {
                    "prefix": self.request.GET.get("q"),
                    "completion": {
                        "field": "suggest",
                        "skip_duplicates": True,
                        "contexts": self.get_suggestion_context(),
                    },
                }
            },
            "_source": False,
        }

        results = es.search(index=OSCAR_PRODUCTS_INDEX_NAME, body=body)
        suggestion = results["suggest"]["autocompletion"][0]

        return [option["text"] for option in suggestion["options"]][0:NUM_SUGGESTIONS]

    # pylint: disable=W0613
    def get(self, request, *args, **kwargs):
        results = self.get_suggestions()
        if results:
            return JsonResponse(results, safe=False)
        else:
            return JsonResponse(results, safe=False, status=400)
