import time

from django.core.management.base import BaseCommand

from oscar.core.loading import get_class, get_model

from oscar_elasticsearch.search import settings

chunked = get_class("search.utils", "chunked")
ProductElasticsearchIndex = get_class("search.api.product", "ProductElasticsearchIndex")

Product = get_model("catalogue", "Product")


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Record the start time for the entire indexing process
        overall_start_time = time.time()

        products = Product.objects.browsable().distinct()
        products_total = products.count()

        # When there are no products, we should still reindex to clear the index
        if products_total == 0:
            ProductElasticsearchIndex().reindex([])
            self.stdout.write(
                self.style.WARNING("no browsable products, index cleared.")
            )
            return

        product_index = ProductElasticsearchIndex()
        product_index.indexer.start()

        total_chunks = products_total / settings.INDEXING_CHUNK_SIZE
        processed_chunks = 0

        for chunk in chunked(products, settings.INDEXING_CHUNK_SIZE):
            chunk_index_time = time.time()
            product_index.reindex(chunk, manage_alias_lifecycle=False)
            processed_chunks += 1
            self.stdout.write(
                self.style.SUCCESS(
                    "Processed chunk %i of %i (%i/%s products indexed) in %.2f seconds"
                    % (
                        processed_chunks,
                        total_chunks,
                        min(
                            processed_chunks * settings.INDEXING_CHUNK_SIZE,
                            products_total,
                        ),
                        products_total,
                        time.time() - chunk_index_time,
                    )
                )
            )

        product_index.indexer.finish()

        self.stdout.write(
            self.style.SUCCESS(
                "\n%i products successfully indexed in %.2f seconds"
                % (products_total, time.time() - overall_start_time)
            )
        )
