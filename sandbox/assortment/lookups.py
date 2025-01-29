from oscar_elasticsearch.search.api.lookup import BaseLookupIndex
from oscar_elasticsearch.search.registry import termlookup_registry

from .models import AssortmentUser


@termlookup_registry.register
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

        return "0" # Id 0 will never exists, hence you see nothing when not logged in.
