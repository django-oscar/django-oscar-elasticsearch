from oscar.core.loading import get_class
from oscar.apps.search.views.catalogue import (
    ProductCategoryView as BaseProductCategoryView,
)

BaseSearchView = get_class("search.views.base", "BaseSearchView")


class ProductCategoryView(BaseProductCategoryView, BaseSearchView):
    def get_queryset(self):
        qs = super().get_queryset()
        categories = self.category.get_descendants_and_self()
        return qs.filter(categories__in=categories)
