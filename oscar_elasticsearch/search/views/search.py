from oscar.apps.search.views.search import FacetedSearchView as BaseFacetedSearchView


class FacetedSearchView(BaseFacetedSearchView):
    def get_elasticsearch_body(self):
        return {
            "query": {
                "multi_match": {
                    "query": self.request.GET.get("q"),
                    "fields": [
                        "_all_text",
                        "_edgengrams",
                        "upc",
                        "title",
                        "title.reversed",
                    ],
                }
            }
        }
