from django.utils.crypto import get_random_string

from elasticsearch.helpers import bulk
from elasticsearch.exceptions import RequestError, NotFoundError

from extendedsearch.backends import get_search_backend

SearchBackend = get_search_backend()

es = SearchBackend.es


class Indexer(object):
    def __init__(self, name, mappings, settings):
        self.name = name
        self.alias_name = "%s_%s" % (name, get_random_string(7).lower())
        self.mappings = mappings
        self.settings = settings

    def execute(self, objects):
        self.start()
        self.bulk_index(objects)
        self.finish()

    def start(self):
        # Create alias
        self.create(self.alias_name)

    def bulk_index(self, objects):
        bulk(es, objects, ignore=[400])

    def finish(self):
        es.indices.refresh(self.alias_name)

        # Check if alias exists for indice
        if es.indices.exists_alias(name=self.name):
            # Get alisases
            aliased_indices = es.indices.get_alias(name=self.name).keys()

            # Link the new alias to the old indice
            es.indices.put_alias(name=self.name, index=self.alias_name)

            # Cleanup old aliased
            for index in aliased_indices:
                if index != self.alias_name:
                    self.delete(index)
        else:
            self.delete(self.name)

            # No indices yet, make alias from original name to alias name
            es.indices.put_alias(name=self.name, index=self.alias_name)

    def create(self, name):
        return es.indices.create(
            index=name, body={"settings": self.settings, "mappings": self.mappings}
        )

    def delete(self, name):
        try:
            es.indices.delete(name)
        except NotFoundError:
            pass
