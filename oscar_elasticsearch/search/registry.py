class ElasticsearchRegistry:
    _indexes = []

    def register(self, cls):
        self._indexes.append(cls)

    @property
    def indexes(self):
        return self._indexes


elasticsearch_registry = ElasticsearchRegistry()
