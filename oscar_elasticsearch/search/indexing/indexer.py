from odin.codecs import dict_codec

from django.utils.crypto import get_random_string
from django.db import transaction

from oscar.core.loading import get_class, get_model

from elasticsearch.helpers import bulk
from elasticsearch.exceptions import NotFoundError

es = get_class("search.backend", "es")
OSCAR_PRODUCTS_INDEX_NAME = get_class(
    "search.indexing.settings", "OSCAR_PRODUCTS_INDEX_NAME"
)
OSCAR_CATEGORIES_INDEX_NAME = get_class(
    "search.indexing.settings", "OSCAR_CATEGORIES_INDEX_NAME"
)
get_categories_index_mapping = get_class(
    "search.indexing.settings", "get_categories_index_mapping"
)
get_products_index_mapping = get_class(
    "search.indexing.settings", "get_products_index_mapping"
)
get_oscar_index_settings = get_class(
    "search.indexing.settings", "get_oscar_index_settings"
)

OSCAR_INDEX_SETTINGS = get_oscar_index_settings()

Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")


class Indexer(object):
    def __init__(self, name, mappings, settings):
        self.name = name
        self.alias_name = "%s_%s" % (name, get_random_string(7).lower())
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

        # pylint: disable=W0106
        [obj.update({"_index": current_alias}) for obj in objects]
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


class ESModelIndexer:
    index_name = None
    index_mappings = None
    index_settings = None

    def __init__(self):
        self.indexer = Indexer(
            self.index_name, self.index_mappings, self.index_settings
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


class ESProductIndexer(ESModelIndexer):
    index_name = OSCAR_PRODUCTS_INDEX_NAME
    index_mappings = get_products_index_mapping()
    index_settings = OSCAR_INDEX_SETTINGS

    def get_es_data_from_objects(self, object_ids):
        from oscar_odin.mappings import catalogue

        ProductElasticSearchMapping = get_class(
            "search.mappings.products", "ProductElasticSearchMapping"
        )

        with transaction.atomic():
            products = Product.objects.filter(pk__in=object_ids).select_for_update()

            product_resources = catalogue.product_queryset_to_resources(products)

            product_resources = ProductElasticSearchMapping.apply(product_resources)

            return dict_codec.dump(product_resources, include_type_field=False)


class ESCategoryIndexer(ESModelIndexer):
    index_name = OSCAR_CATEGORIES_INDEX_NAME
    index_mappings = get_categories_index_mapping()
    index_settings = OSCAR_INDEX_SETTINGS

    def get_es_data_from_objects(self, object_ids):
        from oscar_odin.mappings import catalogue

        CategoryMapping = get_class("search.mappings.categories", "CategoryMapping")

        with transaction.atomic():
            categories = Category.objects.filter(pk__in=object_ids).select_for_update()

            category_resources = catalogue.CategoryToResource.apply(categories)

            category_resources = CategoryMapping.apply(category_resources)

            return dict_codec.dump(category_resources, include_type_field=False)
