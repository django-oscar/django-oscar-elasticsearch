from ocyan.core.fender import config
from ocyan.core.utils import merge_dicts


OSCAR_INDEX_SETTINGS = {
    "analysis": {
        "analyzer": {
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
            "ngram_tokenizer": {"type": "nGram", "min_gram": 3, "max_gram": 15},
            "edgengram_tokenizer": {
                "type": "edgeNGram",
                "min_gram": 2,
                "max_gram": 15,
                "side": "front",
            },
        },
        "filter": {
            "ngram": {"type": "nGram", "min_gram": 3, "max_gram": 15},
            "edgengram": {"type": "edgeNGram", "min_gram": 1, "max_gram": 15},
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
    "index": {"number_of_shards": 1},
}


# OSCAR_INDEX_MAPPING = {
#     "doc": {
#         "properties": {
#             "pk": {"type": "integer", "store": True},
#             "content_type": {"type": "keyword"},
#             "title": {
#                 "type": "text",
#                 "analyzer": "edgengram_analyzer",
#                 "search_analyzer": "standard",
#                 "fields": {
#                     "reversed": {
#                         "type": "text",
#                         "analyzer": "reversed_edgengram_analyzer",
#                         "search_analyzer": "standard",
#                     }
#                 },
#                 "copy_to": "_all_text",
#             },
#             "is_public": {"type": "boolean"},
#             "upc": {"type": "text", "analyzer": "keyword", "copy_to": "_all_text"},
#             "description": {
#                 "type": "text",
#                 "analyzer": "edgengram_analyzer",
#                 "search_analyzer": "standard",
#                 "copy_to": "_all_text",
#             },
#             "categories": {
#                 "type": "nested",
#                 "properties": {
#                     "description": {
#                         "type": "text",
#                         "analyzer": "edgengram_analyzer",
#                         "search_analyzer": "standard",
#                         "copy_to": "_all_text",
#                     },
#                     "slug": {"type": "text", "copy_to": "_all_text"},
#                     "full_name": {
#                         "type": "text",
#                         "copy_to": "_all_text",
#                     },
#                     "absolute_url": {
#                         "type": "text",
#                         "copy_to": "_all_text",
#                     },
#                 },
#             },
#             "stockrecords": {
#                 "type": "nested",
#                 "properties": {
#                     "price_currency": {"type": "keyword"},
#                     "partner_sku": {"type": "text", "copy_to": "_all_text"},
#                     "partner_id": {"type": "integer"},
#                     "num_in_stock": {"type": "integer"},
#                 },
#             },
#             "parent_id": {"type": "integer"},
#             "structure": {"type": "keyword"},
#             "is_standalone": {"type": "boolean"},
#             "slug": {"type": "keyword"},
#             "rating": {"type": "double"},
#             "date_created": {"type": "date"},
#             "date_updated": {"type": "date"},
#             "priority": {"type": "integer"},
#             "_all_text": {"type": "text"},
#         }
#     }
# }


OSCAR_INDEX_MAPPING = {
    "doc": {
        "properties": {
            "id": {"type": "integer", "store": True},
            "content_type": {"type": "keyword", "store": True},
            "title": {
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
                "copy_to": "_all_text",
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
            "slug": {"type": "text", "copy_to": "_all_text"},
            "_all_text": {"type": "text"},
        }
    }
}

OSCAR_PRODUCTS_INDEX_MAPPING = merge_dicts(
    OSCAR_INDEX_MAPPING,
    {
        "doc": {
            "properties": {
                "parent_id": {"type": "integer"},
                "structure": {"type": "text", "copy_to": "_all_text"},
                "rating": {"type": "float"},
                "priority": {"type": "integer"},
                "price": {"type": "double"},
                "num_available": {"type": "integer"},
                "currency": {"type": "text", "copy_to": "_all_text"},
                "date_created": {"type": "date"},
                "date_updated": {"type": "date"},
                "string_attrs": {"type": "text", "copy_to": "_all_text"},
                "facets": {"type": "nested"},
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
                            "copy_to": "_all_text",
                        },
                    },
                },
            }
        }
    },
    overwrite=True,
)


OSCAR_CATEGORIES_INDEX_MAPPING = merge_dicts(
    OSCAR_INDEX_MAPPING,
    {
        "doc": {
            "properties": {"full_name": {"type": "text"}, "full_slug": {"type": "text"}}
        }
    },
    overwrite=True,
)


project_name = config.get("django", "name").lower()
OSCAR_PRODUCTS_INDEX_NAME = "%s__catalogue_product" % project_name
OSCAR_CATEGORIES_INDEX_NAME = "%s__catalogue_category" % project_name
