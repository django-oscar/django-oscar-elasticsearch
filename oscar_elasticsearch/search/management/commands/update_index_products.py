from django.core.management.base import BaseCommand

from oscar.core.loading import get_class, get_model

ProductElasticsearchIndex = get_class("search.api.product", "ProductElasticsearchIndex")

Product = get_model("catalogue", "Product")


class Command(BaseCommand):
    def handle(self, *args, **options):
        products = Product.objects.browsable()
        ProductElasticsearchIndex().reindex(products)
        self.stdout.write(
            self.style.SUCCESS("%i products successfully indexed" % products.count())
        )
