from django.core.management.base import BaseCommand

from oscar.core.loading import get_class, get_model

chunked = get_class("search.utils", "chunked")
ProductElasticsearchIndex = get_class("search.api.product", "ProductElasticsearchIndex")

Product = get_model("catalogue", "Product")


class Command(BaseCommand):
    def handle(self, *args, **options):
        products = Product.objects.browsable()

        for chunk in chunked(products, 100):
            ProductElasticsearchIndex().reindex(chunk)

        self.stdout.write(
            self.style.SUCCESS("%i products successfully indexed" % products.count())
        )
