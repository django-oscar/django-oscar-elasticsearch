from oscar_elasticsearch.search.settings import (
    INDEX_PREFIX,
    FACETS,
    AUTOCOMPLETE_CONTEXTS,
)


def get_oscar_index_settings():
    return {
        "analysis": {
            "analyzer": {
                "case_insensitive": {"tokenizer": "keyword", "filter": ["lowercase"]},
                "ngram_analyzer": {
                    "type": "custom",
                    "tokenizer": "lowercase",
                    "filter": ["asciifolding", "ngram"],
                },
                "edgengram_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "asciifolding",
                        "edgengram",
                        "lowercase",
                        "asciifolding",
                        "edgengram",
                    ],
                    "char_filter": ["non_ascii_character_filter_mapping"],
                },
                "reversed_edgengram_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding", "reversed_edgengram"],
                    "char_filter": ["non_ascii_character_filter_mapping"],
                },
                "standard": {
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"],
                    "char_filter": ["non_ascii_character_filter_mapping"],
                },
            },
            "tokenizer": {
                "ngram_tokenizer": {"type": "ngram", "min_gram": 3, "max_gram": 15},
                "edgengram_tokenizer": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 15,
                    "side": "front",
                },
            },
            "filter": {
                "ngram": {"type": "ngram", "min_gram": 3, "max_gram": 15},
                "edgengram": {"type": "edge_ngram", "min_gram": 1, "max_gram": 15},
                "reversed_edgengram": {
                    "type": "edge_ngram",
                    "min_gram": 3,
                    "max_gram": 15,
                    "side": "back",
                },
            },
            "char_filter": {
                "non_ascii_character_filter_mapping": {
                    "type": "mapping",
                    "mappings": ["’ => '"],
                }
            },
        },
        "index": {"number_of_shards": 1, "max_ngram_diff": 15},
    }


OSCAR_INDEX_MAPPING = {
    "properties": {
        "id": {"type": "integer", "store": True},
        "content_type": {"type": "keyword", "store": True},
        "title": {
            "type": "text",
            "analyzer": "case_insensitive",
            "fielddata": True,
            "copy_to": "_all_text",
        },
        "search_title": {
            "type": "text",
            "analyzer": "edgengram_analyzer",
            "search_analyzer": "standard",
            "fields": {
                "reversed": {
                    "type": "text",
                    "analyzer": "reversed_edgengram_analyzer",
                    "search_analyzer": "standard",
                }
            },
        },
        "is_public": {"type": "boolean"},
        "code": {"type": "text", "analyzer": "keyword", "copy_to": "_all_text"},
        "slug": {"type": "text", "copy_to": "_all_text"},
        "description": {
            "type": "text",
            "analyzer": "edgengram_analyzer",
            "search_analyzer": "standard",
            "copy_to": "_all_text",
        },
        "absolute_url": {"type": "text"},
        "_all_text": {"type": "text"},
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

            attrs_properties[name] = {"type": facet_type}

    return attrs_properties


def get_products_index_mapping():
    OSCAR_PRODUCTS_INDEX_MAPPING = OSCAR_INDEX_MAPPING.copy()

    OSCAR_PRODUCTS_INDEX_MAPPING["properties"].update(
        {
            "parent_id": {"type": "integer"},
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
            "facets": {"type": "nested"},
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
                    "full_name": {
                        "type": "text",
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
