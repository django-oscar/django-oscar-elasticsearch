from django.core.management.base import BaseCommand

from oscar.core.loading import get_class, get_model

ProductElasticSearchApi = get_class("search.api.product", "ProductElasticSearchApi")

Product = get_model("catalogue", "Product")


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("--" * 25)
        product_ids = Product.objects.browsable().values_list("pk", flat=True)

        ProductElasticSearchApi().reindex(product_ids)
