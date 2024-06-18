from django.core.management.base import BaseCommand

from oscar.core.loading import get_class, get_model

CategoryElasticsearchIndex = get_class(
    "search.api.category", "CategoryElasticsearchIndex"
)

Category = get_model("catalogue", "Category")


class Command(BaseCommand):
    def handle(self, *args, **options):
        categories = Category.objects.browsable()
        CategoryElasticsearchIndex().reindex(categories)
        self.stdout.write(
            self.style.SUCCESS(
                "%i categories successfully indexed" % categories.count()
            )
        )
