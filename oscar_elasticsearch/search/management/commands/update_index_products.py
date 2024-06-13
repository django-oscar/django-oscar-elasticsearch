from django.core.management.base import BaseCommand

from oscar.core.loading import get_class, get_model

ProductElasticsearchIndex = get_class("search.api.product", "ProductElasticsearchIndex")

Product = get_model("catalogue", "Product")


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("--" * 25)
        products = Product.objects.browsable()
        ProductElasticsearchIndex().reindex(products)
