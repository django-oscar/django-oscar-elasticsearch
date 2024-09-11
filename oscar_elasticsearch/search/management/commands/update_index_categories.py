from django.core.management.base import BaseCommand

from oscar.core.loading import get_class, get_model

from oscar_elasticsearch.search import settings

chunked = get_class("search.utils", "chunked")
CategoryElasticsearchIndex = get_class(
    "search.api.category", "CategoryElasticsearchIndex"
)

Category = get_model("catalogue", "Category")


class Command(BaseCommand):
    def handle(self, *args, **options):
        categories = Category.objects.browsable()

        with CategoryElasticsearchIndex().reindex() as index:
            for chunk in chunked(categories, settings.INDEXING_CHUNK_SIZE):
                index.reindex_objects(chunk)
                self.stdout.write(".", ending="")
                self.stdout.flush()  # Ensure the dots are displayed immediately

        self.stdout.write(
            self.style.SUCCESS(
                "\n%i categories successfully indexed" % categories.count()
            )
        )
