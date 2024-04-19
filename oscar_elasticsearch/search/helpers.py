from django.db import transaction

from oscar.core.loading import get_model, get_class

chunked = get_class("search.utils", "chunked")
Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")

ESProductIndexer = get_class("search.indexing", "ESProductIndexer")
ESCategoryIndexer = get_class("search.indexing", "ESCategoryIndexer")


def update_index_category(category_id):
    with transaction.atomic():
        update_index_categories([category_id])

        product_ids = list(
            Product.objects.filter(categories__id=category_id).values_list(
                "pk", flat=True
            )
        )
        update_index_products(product_ids)


def update_index_categories(category_ids, update_products=True):
    product_ids = set()

    for chunk in chunked(category_ids, 100):
        with transaction.atomic():
            ESCategoryIndexer().update_or_create_objects(chunk)

            if update_products:
                product_ids.update(
                    set(
                        Product.objects.filter(
                            categories__id__in=category_ids
                        ).values_list("pk", flat=True)
                    )
                )

    if product_ids and update_products:
        update_index_products(list(product_ids))


def update_index_product(product_id):
    update_index_products([product_id])


def update_index_products(product_ids):
    for chunk in chunked(product_ids, 100):
        with transaction.atomic():
            ESProductIndexer().update_or_create_objects(chunk)
