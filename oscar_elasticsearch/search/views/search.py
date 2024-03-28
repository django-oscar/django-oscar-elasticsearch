from oscar.apps.search.views.search import FacetedSearchView as BaseFacetedSearchView


class FacetedSearchView(BaseFacetedSearchView):
    def get_elasticsearch_body(self, selected_facets={}):
        body = super().get_elasticsearch_body(selected_facets=selected_facets)

        body["query"]["bool"]["filter"].append(
            {
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
        )

        return body
