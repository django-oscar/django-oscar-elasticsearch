from oscar.core.loading import get_class

from oscar_elasticsearch.search.api.lookup import BaseLookupIndex
from oscar_elasticsearch.search.registry import elasticsearch_registry

from django.contrib.auth.models import User

BaseElasticSearchApi = get_class("search.api.search", "BaseElasticSearchApi")
ESModelIndexer = get_class("search.indexing.indexer", "ESModelIndexer")

from .models import AssortmentUser


@elasticsearch_registry.register
class UserProductAssortmentIndex(BaseLookupIndex):
    INDEX_NAME = "user_product_assortment"
    LOOKUP_PATH = "product_ids"
    Model = AssortmentUser

    def make_documents(self, objects):
        documents = []

        for obj in objects:
            documents.append(
                {
                    "_id": obj.user.id,
                    self.LOOKUP_PATH: list(obj.products.all().values_list("product_id", flat=True))
                }
            )

        return documents
        
    def get_lookup_id(self, field_to_filter, **kwargs):
        request = kwargs.get("request", None)
        if request and request.user.is_authenticated:
            return str(request.user.id)

        return None  # Returning None will result in not logged in users to see the entire catalogue


@elasticsearch_registry.register
class UserIndex(BaseElasticSearchApi, ESModelIndexer):
    INDEX_NAME = "users"
    Model = User
    INDEX_MAPPING = {
        "properties": {
            "name": {"type": "text"},
            "email": {"type": "text"},
        }
    }
    INDEX_SETTINGS = {}
    
    def make_documents(self, objects):
        return [
            {
                "name": user.get_full_name(),
                "email": user.email,
            } for user in objects
        ]
