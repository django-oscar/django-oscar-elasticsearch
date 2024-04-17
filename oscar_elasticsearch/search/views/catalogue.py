from oscar.apps.search.views.catalogue import (
    ProductCategoryView as BaseProductCategoryView,
)


class ProductCategoryView(BaseProductCategoryView):
    def get_default_filters(self):
        filters = super().get_default_filters()

        category_ids = self.category.get_descendants_and_self().values_list(
            "pk", flat=True
        )

        filters.append(
            {
                "nested": {
                    "path": "categories",
                    "query": {"terms": {"categories.id": list(category_ids)}},
                    "inner_hits": {"size": 0},
                }
            }
        )

        return filters
