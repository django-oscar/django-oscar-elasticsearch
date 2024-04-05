from django.core.management.base import BaseCommand

from oscar.core.loading import get_class, get_model

ESCategoryIndexer = get_class("search.indexing", "ESCategoryIndexer")

Category = get_model("catalogue", "Category")


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("--" * 25)
        category_ids = Category.objects.browsable().values_list("pk", flat=True)

        ESCategoryIndexer().reindex(category_ids)
