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

        # When there are no categories, we should still reindex to clear the index
        if not categories:
            CategoryElasticsearchIndex().reindex(categories)
            self.stdout.write(
                self.style.WARNING("no browsable categories, index cleared.")
            )
            return

        category_index = CategoryElasticsearchIndex()
        category_index.indexer.start()

        for chunk in chunked(categories, settings.INDEXING_CHUNK_SIZE):
            category_index.reindex(chunk, manage_alias_lifecycle=False)

        category_index.indexer.finish()

        self.stdout.write(
            self.style.SUCCESS(
                "\n%i categories successfully indexed" % categories.count()
            )
        )
