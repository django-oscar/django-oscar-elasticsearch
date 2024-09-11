from odin.codecs import dict_codec

from oscar.core.loading import get_class, get_model

# this index name is retrived with get_class because of i18n but it might be removed later
OSCAR_CATEGORIES_INDEX_NAME = get_class(
    "search.indexing.settings", "OSCAR_CATEGORIES_INDEX_NAME"
)
get_categories_index_mapping = get_class(
    "search.indexing.settings", "get_categories_index_mapping"
)
get_oscar_index_settings = get_class(
    "search.indexing.settings", "get_oscar_index_settings"
)


OSCAR_INDEX_SETTINGS = get_oscar_index_settings()

BaseElasticSearchApi = get_class("search.api.search", "BaseElasticSearchApi")
ESModelIndexer = get_class("search.indexing.indexer", "ESModelIndexer")

Category = get_model("catalogue", "Category")


class CategoryElasticsearchIndex(BaseElasticSearchApi, ESModelIndexer):
    INDEX_NAME = OSCAR_CATEGORIES_INDEX_NAME
    INDEX_MAPPING = get_categories_index_mapping()
    INDEX_SETTINGS = OSCAR_INDEX_SETTINGS
    Model = Category

    def make_documents(self, objects):
        from oscar_odin.mappings import catalogue

        CategoryElasticSearchMapping = get_class(
            "search.mappings.categories", "CategoryElasticSearchMapping"
        )

        category_resources = catalogue.CategoryToResource.apply(objects)
        category_document_resources = CategoryElasticSearchMapping.apply(
            category_resources
        )

        return dict_codec.dump(category_document_resources, include_type_field=False)
