from oscar.apps.search.views.catalogue import (
    ProductCategoryView as BaseProductCategoryView,
)


class ProductCategoryView(BaseProductCategoryView):
    def get_elasticsearch_body(self):
        category_ids = self.category.get_descendants_and_self().values_list(
            "pk", flat=True
        )

        return {
            "query": {
                "nested": {
                    "path": "categories",
                    "query": {"terms": {"categories.id": list(category_ids)}},
                    "inner_hits": {"size": 0},
                }
            }
        }
