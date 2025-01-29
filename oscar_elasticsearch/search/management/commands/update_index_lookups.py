from django.core.management.base import BaseCommand

from oscar.core.loading import get_class

from oscar_elasticsearch.search import settings
from oscar_elasticsearch.search.registry import termlookup_registry

chunked = get_class("search.utils", "chunked")


class Command(BaseCommand):
    def handle(self, *args, **options):
        for Lookup in termlookup_registry.lookups:
            self.stdout.write(
                self.style.SUCCESS("\n Star indexing lookup: %s" % Lookup)
            )

            lookup_index = Lookup()
            lookup_queryset = lookup_index.get_queryset()
            with lookup_index.reindex() as index:
                for chunk in chunked(lookup_queryset, settings.INDEXING_CHUNK_SIZE):
                    index.reindex_objects(chunk)
                    self.stdout.write(".", ending="")
                    self.stdout.flush()  # Ensure the dots are displayed immediately

            self.stdout.write(
                self.style.SUCCESS(
                    "\n%i lookups successfully indexed" % lookup_queryset.count()
                )
            )
