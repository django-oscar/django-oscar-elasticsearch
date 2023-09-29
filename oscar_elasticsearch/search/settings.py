OSCAR_INDEX_SETTINGS = {
    "analysis": {
        "analyzer": {
            "upc_analyzer": {
                "type": "custom",
                "tokenizer": "upc_tokenizer",
                "filter": ["lowercase"],
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
            "lowercasewhitespace": {
                "tokenizer": "whitespace",
                "filter": ["lowercase"],
            },
        },
        "tokenizer": {
            "upc_tokenizer": {"type": "edge_ngram", "min_gram": 2, "max_gram": 15}
        },
        "filter": {
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
    "index": {"number_of_shards": 1},
}


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
            "upc": {"type": "text", "analyzer": "keyword", "copy_to": "_all_text"},
            "description": {
                "type": "text",
                "analyzer": "edgengram_analyzer",
                "search_analyzer": "standard",
                "copy_to": "_all_text",
            },
            "_all_text": {"type": "text"},
        }
    }
}

OSCAR_INDEX_NAME = "django-oscar-elasticsearch-products"
