import threading
from oscar.core.loading import get_classes

update_index_products, update_index_categories = get_classes(
    "search.helpers", ["update_index_products", "update_index_categories"]
)


class UpdateIndex(threading.local):
    def __init__(self):
        super().__init__()
        self._products = set()
        self._categories = set()

    def push_category(self, *categories):
        self._categories.update(categories)

    def push_product(self, *products):
        self._products.update(products)

    # pylint: disable=unused-argument
    def synchronize_searchindex(self, **kwargs):
        categories = list(self._categories)
        self._categories = set()
        products = list(self._products)
        self._products = set()
        update_index_products(products)
        update_index_categories(categories)
