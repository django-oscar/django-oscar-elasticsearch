from django.utils.translation import gettext_lazy as _
from django.views import View
from django.http import JsonResponse

from oscar.core.loading import get_model, get_class

from oscar_elasticsearch.search.settings import (
    NUM_SUGGESTIONS,
    SUGGESTION_STATUS_FILTER,
)

es = get_class("search.backend", "es")


class CatalogueAutoCompleteView(View):
    def get_suggestions(self):
        body = {
            "query": {
                "bool": {
                    "must": {
                        "match_phrase_prefix": {
                            "autocomplete_title": self.request.GET.get("q")
                        }
                    },
                    "filter": {"term": {"status": SUGGESTION_STATUS_FILTER}},
                }
            }
        }

        results = es.search(body=body)

        return [hit["_source"]["title"] for hit in results["hits"]["hits"]][
            0:NUM_SUGGESTIONS
        ]

    # pylint: disable=W0613
    def get(self, request, *args, **kwargs):
        results = self.get_suggestions()
        if results:
            return JsonResponse(results, safe=False)
        else:
            return JsonResponse(results, safe=False, status=400)
