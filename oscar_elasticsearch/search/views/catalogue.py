from oscar.apps.search.views.catalogue import (
    ProductCategoryView as BaseProductCategoryView,
)


class ProductCategoryView(BaseProductCategoryView):
    def get_elasticsearch_body(self, selected_facets={}):
        body = super().get_elasticsearch_body(selected_facets=selected_facets)

        category_ids = self.category.get_descendants_and_self().values_list(
            "pk", flat=True
        )

        body["query"]["bool"]["filter"].append(
            {
                "nested": {
                    "path": "categories",
                    "query": {"terms": {"categories.id": list(category_ids)}},
                    "inner_hits": {"size": 0},
                }
            }
        )

        return body
