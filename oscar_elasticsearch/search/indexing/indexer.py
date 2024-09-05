from contextlib import contextmanager

from django.utils.crypto import get_random_string
from django.utils.text import format_lazy
from django.utils.encoding import force_str

from oscar.core.loading import get_class

from elasticsearch.helpers import bulk
from elasticsearch.exceptions import NotFoundError

from oscar_elasticsearch.search.api.base import BaseModelIndex

es = get_class("search.backend", "es")


class Indexer(object):
    def __init__(self, name, mappings, settings):
        self.name = name
        self.alias_name = format_lazy(
            "{name}_{suffix}", name=name, suffix=get_random_string(7).lower()
        )
        self.mappings = mappings
        self.settings = settings

    def execute(self, documents):
        self.bulk_index(documents, self.alias_name)

    def start(self):
        # Create alias
        self.create(self.alias_name)

    def index(self, _id, document, current_alias=None):
        if current_alias is None:
            current_alias = self.get_current_alias()

        _index = force_str(current_alias)

        es.index(index=_index, id=_id, document=document, ignore=[400])

    def bulk_index(self, documents, current_alias=None):
        if current_alias is None:
            current_alias = self.get_current_alias()

        _index = force_str(current_alias)

        docs = []
        for doc in documents:
            doc["_index"] = _index
            docs.append(doc)

        bulk(es, docs, ignore=[400])

    def get_current_alias(self):
        aliasses = list(es.indices.get_alias(name=self.name).keys())
        if aliasses:
            return aliasses[0]

        return self.alias_name

    def finish(self):
        es.indices.refresh(index=self.alias_name)

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
            es.indices.delete(index=name)
        except NotFoundError:
            pass

    def delete_doc(self, _id):
        try:
            return es.delete(index=self.get_current_alias(), id=_id)
        except NotFoundError:
            pass


class ESModelIndexer(BaseModelIndex):
    def __init__(self):
        super().__init__()
        self.indexer = Indexer(
            self.get_index_name(), self.get_index_mapping(), self.get_index_settings()
        )

    def make_documents(self, objects):
        raise NotImplementedError(
            "Please implement `make_documents` on your indexer class"
        )

    def update_or_create(self, objects):
        es_data = self.make_documents(objects)
        return self.indexer.bulk_index(es_data)

    def index(self, obj):
        (es_data,) = self.make_documents([obj])
        self.indexer.index(obj.id, es_data["_source"])

    @contextmanager
    def reindex(self):
        """
        Example usage:
        with CategoryElasticsearchIndex().reindex() as index:
            for chunk in chunked(categories, settings.INDEXING_CHUNK_SIZE):
                index.reindex_objects(chunk)
        """
        self.indexer.start()

        try:
            yield self
        finally:
            self.indexer.finish()

    def reindex_objects(self, objects):
        es_data = self.make_documents(objects)
        return self.indexer.execute(es_data)

    def delete(self, _id):
        return self.indexer.delete_doc(_id)
