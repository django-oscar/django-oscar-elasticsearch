from django.db import transaction

from oscar.core.loading import get_model, get_class

from extendedsearch import index
from extendedsearch.backends import get_search_backend

chunked = get_class("search.utils", "chunked")
ProductProxy = get_model("search", "ProductProxy")


def add_bulk(products):
    backend = get_search_backend()
    for chunk in chunked(products, 100):
        backend.add_bulk(ProductProxy, chunk)


def update_index_category(category_id):
    with transaction.atomic():
        # make sure all transactions involving this category have finished before
        # updating the index.
        products = list(
            ProductProxy.objects.filter(categories__id=category_id).select_for_update()
        )
        add_bulk(products)


def update_index_categories(category_ids):
    with transaction.atomic():
        # make sure all transactions involving this category have finished before
        # updating the index.
        products = list(
            ProductProxy.objects.filter(
                categories__id__in=category_ids
            ).select_for_update()
        )
        add_bulk(products)


def update_index_product(product_id):
    with transaction.atomic():
        # make sure all transactions involving this product have finished before
        # updating the index.
        products = ProductProxy.objects.filter(pk=product_id).select_for_update()
        try:
            product = products.get()
            index.insert_or_update_object(product)
        except ProductProxy.DoesNotExist:
            pass  # if the product has been deleted, well so be it.


def update_index_products(product_ids):
    for chunk in chunked(product_ids, 100):
        with transaction.atomic():
            # make sure all transactions involving this chunk have finished before
            # updating the index.
            products = (
                ProductProxy.get_indexed_objects()
                .filter(pk__in=chunk)
                .select_for_update()
            )
            add_bulk(products)
