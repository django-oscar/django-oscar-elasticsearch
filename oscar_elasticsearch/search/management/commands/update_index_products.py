from django.core.management.base import BaseCommand

from oscar.core.loading import get_class, get_model

ESProductIndexer = get_class("search.indexing", "ESProductIndexer")

Product = get_model("catalogue", "Product")


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("--" * 25)
        product_ids = Product.objects.browsable().values_list("pk", flat=True)

        ESProductIndexer().reindex(product_ids)
