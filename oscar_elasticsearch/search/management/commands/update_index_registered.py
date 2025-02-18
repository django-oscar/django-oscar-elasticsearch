from oscar_elasticsearch.search.registry import elasticsearch_registry
from django.core.management.base import BaseCommand

from oscar.core.loading import get_class

from oscar_elasticsearch.search import settings

chunked = get_class("search.utils", "chunked")


class Command(BaseCommand):
    def handle(self, *args, **options):
        for Index in elasticsearch_registry.indexes:
            index = Index()

            self.stdout.write(
                self.style.SUCCESS(
                    "\n Start indexing index: %s" % index.get_index_name()
                )
            )

            index_queryset = index.get_queryset()
            with index.reindex() as index:
                for chunk in chunked(index_queryset, settings.INDEXING_CHUNK_SIZE):
                    index.reindex_objects(chunk)
                    self.stdout.write(".", ending="")
                    self.stdout.flush()  # Ensure the dots are displayed immediately

            self.stdout.write(
                self.style.SUCCESS(
                    "\n%i %s successfully indexed"
                    % (index_queryset.count(), index.get_index_name())
                )
            )
