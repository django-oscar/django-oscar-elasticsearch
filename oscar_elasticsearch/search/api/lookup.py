from oscar.core.loading import get_class

BaseElasticSearchApi = get_class("search.api.search", "BaseElasticSearchApi")
ESModelIndexer = get_class("search.indexing.indexer", "ESModelIndexer")


class BaseLookupIndex(BaseElasticSearchApi, ESModelIndexer):
    """
    Subclass this class to create a custom lookup for your index.
    https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-terms-query.html#query-dsl-terms-lookup

    set LOOKUP_PATH as the field you want to save on the lookup index, that you can use to filter stuff on the main index you're using

    Example for make_documents:
    def make_documents(self, objects):
        documents = []

        for user in objects:
            documents.append([
                    {
                        "_id": user.id,
                        self.LOOKUP_PATH: [p.id, for p in user.products]
                    }
                ]
            )

        return documents

    """

    LOOKUP_PATH = None
    INDEX_SETTINGS = {}

    def get_index_mapping(self):
        if self.LOOKUP_PATH is None:
            raise NotImplementedError("Please set LOOKUP_PATH on your lookup index")

        return {"properties": {self.LOOKUP_PATH: {"type": "keyword"}}}

    def get_lookup_id(self, field_to_filter, **kwargs):
        raise NotImplementedError(
            """
            Please implement 'get_lookup_id' on your lookup index. 
            Return None to not apply this lookup filter, return the actual id to filter on that id, 
            Id's should always be strings (elasticsearch), never integers
            """
        )

    def get_lookup_query(self, field_to_filter, **kwargs):
        lookup_id = self.get_lookup_id(field_to_filter, **kwargs)

        if lookup_id is not None:
            return {
                "terms": {
                    field_to_filter: {
                        "index": self.get_index_name(),
                        "id": lookup_id,
                        "path": self.LOOKUP_PATH,
                    }
                }
            }

        return None
