import time
from django.core.management.base import BaseCommand
from oscar.core.loading import get_class, get_model
from oscar_elasticsearch.search import settings

chunked = get_class("search.utils", "chunked")
ProductElasticsearchIndex = get_class("search.api.product", "ProductElasticsearchIndex")
Product = get_model("catalogue", "Product")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Run command in debug mode",
        )

    def handle(self, *args, **options):
        if options["debug"]:
            return self.handle_debug()

        products = Product.objects.browsable()
        products_total = products.count()

        with ProductElasticsearchIndex().reindex() as index:
            for chunk in chunked(products, settings.INDEXING_CHUNK_SIZE):
                index.reindex_objects(chunk)
                self.stdout.write(".", ending="")
                self.stdout.flush()  # Ensure the dots are displayed immediately

        self.stdout.write(
            self.style.SUCCESS("\n%i products successfully indexed" % products_total)
        )

    def handle_debug(self):
        """
        Display more detailed information about the indexing process, such as the time it took to index each chunk.
        This is useful when debugging the performance of the indexing process.
        """
        overall_start_time = time.time()
        products = Product.objects.browsable()
        products_total = products.count()
        total_chunks = products_total / settings.INDEXING_CHUNK_SIZE
        processed_chunks = 0

        with ProductElasticsearchIndex().reindex() as index:
            for chunk in chunked(products, settings.INDEXING_CHUNK_SIZE):
                chunk_index_time = time.time()
                index.reindex_objects(chunk)
                processed_chunks += 1
                chunk_duration = time.time() - chunk_index_time

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
                            chunk_duration,
                        )
                    )
                )

        total_duration = time.time() - overall_start_time
        self.stdout.write(
            self.style.SUCCESS(
                "\n%i products successfully indexed in %.2f seconds"
                % (products_total, total_duration)
            )
        )
