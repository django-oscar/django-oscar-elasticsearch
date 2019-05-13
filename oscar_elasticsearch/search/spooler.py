from uwsgidecoratorsfallback import spool
from django.db import connection
from wagtail.search import index
from oscar.core.loading import get_model

ProductProxy = get_model("search", "ProductProxy")


@spool
def update_index(arguments):
    # the spooler is forked so the db connection might be closed
    if not connection.is_usable():
        connection.close()

    category_id = arguments.get("category_id")
    product_id = arguments.get("product_id")

    if category_id is not None:
        products = ProductProxy.objects.filter(categories__id=category_id)
        for product in products:
            index.insert_or_update_object(product)

    if product_id is not None:
        product = ProductProxy.objects.get(pk=product_id)
        index.insert_or_update_object(product)
