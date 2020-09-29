import json
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db import models
from oscar.core.loading import get_model

ProductAttribute = get_model("catalogue", "ProductAttribute")


class Command(BaseCommand):
    """
    Inspect the product attributes to determine facets.

    Usage:

    first run the command without flags to see the attribute and the numbber of
    occurrences. You can now guess which attributes would make good facets.

    next run the command with the --json flag to output facets config, and edit
    it to remove the unwanted facets.

    Last determine if some of the facets are better sorted based on count
    instead of alfabetically and change it like this:

        {
            "name": "afmrugpel",
            "label": "afmrugpel",
            "type": "term",
            "order": { "_count" : "desc" }
        }
    """

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", help="Show facets as json")

    def handle(self, *args, **options):
        facets = defaultdict(int)
        facet_labels = {}
        for code, label, num_products in ProductAttribute.objects.annotate(
            num_products=models.Count("product")
        ).values_list("code", "name", "num_products"):
            facets[code] += num_products
            facet_labels[code] = label

        sorted_facets = sorted(facets.items(), key=lambda x: x[1], reverse=True)
        if options["json"]:
            self.stdout.write(
                json.dumps(
                    [
                        {"name": code, "label": facet_labels[code], "type": "term"}
                        for code, _ in sorted_facets
                    ],
                    indent=4,
                )
            )
        else:
            for code, num_products in sorted_facets:
                self.stdout.write("%s %s\n" % (code, num_products))
