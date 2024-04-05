from oscar_elasticsearch.search.settings import INDEX_PREFIX, FACETS
from oscar.core.loading import get_class


OSCAR_INDEX_SETTINGS = {
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
#                 "copy_to": "_x",
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
    "properties": {
        "id": {"type": "integer", "store": True},
        "content_type": {"type": "keyword", "store": True},
        "title": {"type": "text", "analyzer": "case_insensitive", "fielddata": True},
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

# OSCAR_PRODUCTS_INDEX_MAPPING = OSCAR_INDEX_MAPPING.copy()

# {
#    "doc":{
#       "properties":{
#          "pk":{
#             "type":"keyword",
#             "store":true
#          },
#          "content_type":{
#             "type":"keyword"
#          },
#          "_edgengrams":{
#             "type":"text",
#             "analyzer":"edgengram_analyzer",
#             "search_analyzer":"standard"
#          },
#          "id_filter":{
#             "type":"integer"
#          },
#          "search_productproxy__product_class__name_filter":{
#             "type":"keyword"
#          },
#          "title_filter":{
#             "type":"keyword"
#          },
#          "title":{
#             "type":"text",
#             "analyzer":"edgengram_analyzer",
#             "search_analyzer":"standard",
#             "fields":{
#                "reversed":{
#                   "type":"text",
#                   "analyzer":"reversed_edgengram_analyzer",
#                   "search_analyzer":"standard"
#                }
#             },
#             "copy_to":"_all_text"
#          },
#          "is_public_filter":{
#             "type":"boolean"
#          },
#          "title_edgengrams":{
#             "type":"text",
#             "analyzer":"edgengram_analyzer",
#             "search_analyzer":"standard"
#          },
#          "upc_edgengrams":{
#             "type":"text",
#             "analyzer":"keyword",
#             "search_analyzer":"standard"
#          },
#          "upc_filter":{
#             "type":"keyword"
#          },
#          "upc":{
#             "type":"text",
#             "analyzer":"keyword",
#             "copy_to":"_all_text"
#          },
#          "search_productproxy__child_upc":{
#             "type":"text",
#             "analyzer":"keyword",
#             "copy_to":"_all_text"
#          },
#          "search_productproxy__child_upc_edgengrams":{
#             "type":"text",
#             "analyzer":"keyword",
#             "search_analyzer":"standard"
#          },
#          "description":{
#             "type":"text",
#             "analyzer":"edgengram_analyzer",
#             "search_analyzer":"standard",
#             "copy_to":"_all_text"
#          },
#          "search_productproxy__popularity_filter":{
#             "type":"keyword"
#          },
#          "search_productproxy__price_filter":{
#             "type":"double"
#          },
#          "search_productproxy__is_available_filter":{
#             "type":"boolean"
#          },
#          "search_productproxy__category_id_filter":{
#             "type":"keyword"
#          },
#          "search_productproxy__category_name":{
#             "type":"text",
#             "analyzer":"edgengram_analyzer",
#             "search_analyzer":"standard",
#             "copy_to":"_all_text"
#          },
#          "search_productproxy__category_name_edgengrams":{
#             "type":"text",
#             "analyzer":"edgengram_analyzer",
#             "search_analyzer":"standard"
#          },
#          "categories":{
#             "type":"nested",
#             "properties":{
#                "description":{
#                   "type":"text",
#                   "analyzer":"edgengram_analyzer",
#                   "search_analyzer":"standard",
#                   "copy_to":"_all_text"
#                },
#                "slug":{
#                   "type":"text",
#                   "copy_to":"_all_text"
#                },
#                "catalogue_abstractcategory__full_name":{
#                   "type":"text",
#                   "copy_to":"_all_text"
#                },
#                "catalogue_abstractcategory__get_absolute_url":{
#                   "type":"text",
#                   "copy_to":"_all_text"
#                }
#             }
#          },
#          "stockrecords":{
#             "type":"nested",
#             "properties":{
#                "price_currency_filter":{
#                   "type":"keyword"
#                },
#                "partner_sku":{
#                   "type":"text",
#                   "copy_to":"_all_text"
#                },
#                "partner_id_filter":{
#                   "type":"integer"
#                },
#                "num_in_stock_filter":{
#                   "type":"integer"
#                }
#             }
#          },
#          "parent_id_filter":{
#             "type":"integer"
#          },
#          "structure_filter":{
#             "type":"keyword"
#          },
#          "catalogue_abstractproduct__is_standalone_filter":{
#             "type":"keyword"
#          },
#          "slug_filter":{
#             "type":"keyword"
#          },
#          "rating_filter":{
#             "type":"double"
#          },
#          "date_created_filter":{
#             "type":"date"
#          },
#          "date_updated_filter":{
#             "type":"date"
#          },
#          "search_productproxy__string_attrs":{
#             "type":"text",
#             "copy_to":"_all_text"
#          },
#          "search_productproxy__attrs_filter":{
#             "type":"object",
#             "properties":{
#                "barcode":{
#                   "type":"keyword"
#                },
#                "brand":{
#                   "type":"keyword"
#                },
#                "mpn":{
#                   "type":"keyword"
#                },
#                "size":{
#                   "type":"keyword"
#                }
#             }
#          },
#          "priority_filter":{
#             "type":"integer"
#          },
#          "search_productproxy__status_filter":{
#             "type":"keyword"
#          },
#          "_all_text":{
#             "type":"text"
#          },
#          "title_auto_complete":{
#             "type":"completion",
#             "contexts":[
#                {
#                   "name":"status",
#                   "type":"category",
#                   "path":"search_productproxy__status_filter"
#                }
#             ]
#          },
#          "upc_auto_complete":{
#             "type":"completion",
#             "contexts":[
#                {
#                   "name":"status",
#                   "type":"category",
#                   "path":"search_productproxy__status_filter"
#                }
#             ],
#             "analyzer":"keyword"
#          },
#          "search_productproxy__child_upc_auto_complete":{
#             "type":"completion",
#             "contexts":[
#                {
#                   "name":"status",
#                   "type":"category",
#                   "path":"search_productproxy__status_filter"
#                }
#             ],
#             "analyzer":"keyword"
#          },
#          "search_productproxy__category_name_auto_complete":{
#             "type":"completion",
#             "contexts":[
#                {
#                   "name":"status",
#                   "type":"category",
#                   "path":"search_productproxy__status_filter"
#                }
#             ]
#          }
#       }
#    }
# }


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
        }
    )
    print(OSCAR_PRODUCTS_INDEX_MAPPING)
    return OSCAR_PRODUCTS_INDEX_MAPPING


# print(OSCAR_PRODUCTS_INDEX_MAPPING)
OSCAR_CATEGORIES_INDEX_MAPPING = OSCAR_INDEX_MAPPING.copy()
OSCAR_CATEGORIES_INDEX_MAPPING.update(
    {"properties": {"full_name": {"type": "text"}, "full_slug": {"type": "text"}}}
)

OSCAR_PRODUCTS_INDEX_NAME = "%s__catalogue_product" % INDEX_PREFIX
OSCAR_CATEGORIES_INDEX_NAME = "%s__catalogue_category" % INDEX_PREFIX
