from oscar_elasticsearch.search.utils import get_index_settings
from oscar_elasticsearch.search.settings import (
    INDEX_PREFIX,
    FACETS,
    AUTOCOMPLETE_CONTEXTS,
    MAX_GRAM,
    SEARCH_FIELDS,
)


def get_oscar_index_settings():
    return get_index_settings(MAX_GRAM)


OSCAR_INDEX_MAPPING = {
    "properties": {
        "id": {"type": "integer", "store": True},
        "content_type": {"type": "keyword", "store": True},
        "title": {
            "type": "text",
            "analyzer": "lowercasewhitespace",
            "fielddata": True,
            "copy_to": "_all_text",
            "fields": {"raw": {"type": "keyword"}},
        },
        "search_title": {
            "type": "text",
            "analyzer": "title_analyzer",
            "search_analyzer": "standard",
            "fields": {
                "reversed": {
                    "type": "text",
                    "analyzer": "reversed_title_analyzer",
                    "search_analyzer": "standard",
                }
            },
        },
        "is_public": {"type": "boolean"},
        "code": {"type": "keyword", "copy_to": "_all_text"},
        "slug": {"type": "keyword", "copy_to": "_all_text"},
        "description": {
            "type": "text",
            "analyzer": "standard",
            "copy_to": "_all_text",
        },
        "absolute_url": {"type": "keyword"},
        "_all_text": {"type": "text", "analyzer": "standard"},
    }
}


def get_attributes_to_index():
    attrs_properties = {}

    for facet in FACETS:
        if "attrs." in facet["name"]:
            name = facet["name"].replace("attrs.", "")
            facet_type = "keyword"
            if facet["type"] == "range":
                facet_type = "double"

            attrs_properties[name] = {"type": facet_type, "copy_to": "_all_text"}

    return attrs_properties


def get_products_index_mapping():
    OSCAR_PRODUCTS_INDEX_MAPPING = OSCAR_INDEX_MAPPING.copy()

    OSCAR_PRODUCTS_INDEX_MAPPING["properties"].update(
        {
            "upc": {
                "type": "text",
                "analyzer": "technical_analyzer",
                "fielddata": True,
                "search_analyzer": "technical_search_analyzer",
            },
            "parent_id": {"type": "integer"},
            "product_class": {"type": "keyword"},
            "structure": {"type": "text", "copy_to": "_all_text"},
            "rating": {"type": "float"},
            "priority": {"type": "integer"},
            "price": {"type": "double"},
            "num_available": {"type": "integer"},
            "is_available": {"type": "boolean"},
            "currency": {"type": "text", "copy_to": "_all_text"},
            "date_created": {"type": "date"},
            "date_updated": {"type": "date"},
            "string_attrs": {"type": "text", "copy_to": "_all_text"},
            "popularity": {"type": "integer"},
            "status": {"type": "text"},
            "categories": {
                "type": "nested",
                "properties": {
                    "id": {"type": "integer"},
                    "description": {
                        "type": "text",
                        "copy_to": "_all_text",
                    },
                    "name": {
                        "type": "text",
                        "copy_to": "_all_text",
                    },
                    "ancestor_names": {
                        "type": "text",
                        "copy_to": "_all_text",
                    },
                },
            },
            "attrs": {"type": "object", "properties": get_attributes_to_index()},
            "suggest": {"type": "completion", "contexts": AUTOCOMPLETE_CONTEXTS},
        }
    )

    return OSCAR_PRODUCTS_INDEX_MAPPING


def get_categories_index_mapping():
    OSCAR_CATEGORIES_INDEX_MAPPING = OSCAR_INDEX_MAPPING.copy()
    OSCAR_CATEGORIES_INDEX_MAPPING.update(
        {"properties": {"full_name": {"type": "text"}, "full_slug": {"type": "text"}}}
    )
    return OSCAR_CATEGORIES_INDEX_MAPPING


OSCAR_PRODUCTS_INDEX_NAME = "%s__catalogue_product" % INDEX_PREFIX
OSCAR_CATEGORIES_INDEX_NAME = "%s__catalogue_category" % INDEX_PREFIX
OSCAR_PRODUCT_SEARCH_FIELDS = SEARCH_FIELDS + ["upc^2"]
OSCAR_CATEGORY_SEARCH_FIELDS = SEARCH_FIELDS
