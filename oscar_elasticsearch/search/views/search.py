from django.utils.translation import gettext_lazy as _
from django.views import View
from django.http import JsonResponse

from oscar.core.loading import get_model, get_class

from oscar_elasticsearch.search.settings import NUM_SUGGESTIONS

es = get_class("search.backend", "es")


class CatalogueAutoCompleteView(View):
    def get_suggestions(self):
        body = {
            "query": {
                "match_phrase_prefix": {"autocomplete_title": self.request.GET.get("q")}
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
