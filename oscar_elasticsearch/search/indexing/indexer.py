from django.utils.crypto import get_random_string
from django.utils.text import format_lazy
from django.utils.encoding import force_str

from oscar.core.loading import get_class

from elasticsearch.helpers import bulk
from elasticsearch.exceptions import NotFoundError

es = get_class("search.backend", "es")

BaseElasticSearchClass = get_class("search.api.base", "BaseElasticSearchClass")


class Indexer(object):
    def __init__(self, name, mappings, settings):
        self.name = name
        self.alias_name = format_lazy(
            "{name}_{suffix}", name=name, suffix=get_random_string(7).lower()
        )
        self.mappings = mappings
        self.settings = settings

    def execute(self, objects):
        self.start()
        self.bulk_index(objects, self.alias_name)
        self.finish()

    def start(self):
        # Create alias
        self.create(self.alias_name)

    def bulk_index(self, objects, current_alias=None):
        if current_alias is None:
            current_alias = self.get_current_alias()

        _index = force_str(current_alias)

        # pylint: disable=W0106
        [obj.update({"_index": _index}) for obj in objects]
        bulk(es, objects, ignore=[400])

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


class ESModelIndexer(BaseElasticSearchClass):
    def __init__(self):
        super().__init__()
        self.indexer = Indexer(
            self.get_index_name(), self.get_index_mapping(), self.get_index_settings()
        )

    def get_es_data_from_objects(self, object_ids):
        raise NotImplementedError(
            "Please implement `get_es_data_from_objects` on your indexer class"
        )

    def update_or_create_objects(self, object_ids):
        es_data = self.get_es_data_from_objects(object_ids)
        return self.indexer.bulk_index(es_data)

    def reindex(self, object_ids):
        es_data = self.get_es_data_from_objects(object_ids)
        return self.indexer.execute(es_data)

    def delete(self, _id):
        return self.indexer.delete_doc(_id)
