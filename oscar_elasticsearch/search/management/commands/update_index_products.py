from django.core.management.base import BaseCommand

from oscar.core.loading import get_class, get_model

from oscar_elasticsearch.search import settings

chunked = get_class("search.utils", "chunked")
ProductElasticsearchIndex = get_class("search.api.product", "ProductElasticsearchIndex")

Product = get_model("catalogue", "Product")


class Command(BaseCommand):
    def handle(self, *args, **options):
        products = Product.objects.browsable()

        # When there are no products, we should still reindex to clear the index
        if not products:
            ProductElasticsearchIndex().reindex(products)

        for chunk in chunked(products, settings.INDEXING_CHUNK_SIZE):
            ProductElasticsearchIndex().reindex(chunk)
            self.stdout.write(".", ending="")

        self.stdout.write(
            self.style.SUCCESS("\n%i products successfully indexed" % products.count())
        )
