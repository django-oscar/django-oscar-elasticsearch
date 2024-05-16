from django.core.management.base import BaseCommand

from oscar.core.loading import get_class, get_model

CategoryElasticSearchApi = get_class("search.api.category", "CategoryElasticSearchApi")

Category = get_model("catalogue", "Category")


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("--" * 25)
        category_ids = Category.objects.browsable().values_list("pk", flat=True)

        CategoryElasticSearchApi().reindex(category_ids)
