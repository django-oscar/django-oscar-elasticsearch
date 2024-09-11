from oscar_elasticsearch.search.settings import (
    INDEX_PREFIX,
    FACETS,
    AUTOCOMPLETE_CONTEXTS,
    MAX_GRAM,
    SEARCH_FIELDS,
)


def get_oscar_index_settings():
    return {
        "analysis": {
            "analyzer": {
                # the simplest analyzer most useful for normalizing and splitting a sentence into words
                # this is most likely only used as a search analyzer
                "lowercasewhitespace": {
                    "tokenizer": "whitespace",
                    "filter": ["lowercase", "asciifolding"],
                    "char_filter": ["non_ascii_character_filter_mapping"],
                },
                # this analyzer will keep all punctuation and numbers and make ngrams
                # as small as a single character. Only usefull for upcs and techincal terms
                "technical_analyzer": {
                    "tokenizer": "whitespace",
                    "filter": [
                        "shallow_edgengram",
                        "lowercase",
                        "asciifolding",
                        "max_gram_truncate",
                    ],
                    "char_filter": ["non_ascii_character_filter_mapping"],
                },
                # should be used as the search analyzer for terms analyzed with the
                # technical_analyzer. Will just split the input into words and normalize
                # but keeping in mind the max ngram size.
                "technical_search_analyzer": {
                    "tokenizer": "whitespace",
                    "filter": [
                        "lowercase",
                        "asciifolding",
                        "max_gram_truncate",
                    ],
                    "char_filter": ["non_ascii_character_filter_mapping"],
                },
                # this analyzer is usefull for important textual data like titles,
                # that contain a lot of search terms.
                "title_analyzer": {
                    "tokenizer": "standard",
                    "filter": [
                        "edgengram",
                        "lowercase",
                        "asciifolding",
                        "max_gram_truncate",
                    ],
                },
                # should be used as the search analyzer for terms analyzed with title_analyzer
                "reversed_title_analyzer": {
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "asciifolding",
                        "reversed_edgengram",
                        "max_gram_truncate",
                    ],
                },
                # this analyzer is most usefull for long textual data. punctuation and numbers
                # WILL BE STRIPPED
                "standard": {
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"],
                },
                # This analyzer is usefull for when you need to find really specific data inside some text,
                # for example you have a 'Volvo Penta TAD163532E' code inside your model type and you want it to be found with 'Penta D16'
                # Also use the 'technical_search_analyzer' for this one.
                "technical_title_analyzer": {
                    "tokenizer": "whitespace",
                    "filter": [
                        "ngram",
                        "lowercase",
                        "asciifolding",
                        "max_gram_truncate",
                    ],
                },
            },
            "tokenizer": {
                "ngram_tokenizer": {"type": "ngram", "min_gram": 3, "max_gram": 15},
                "edgengram_tokenizer": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": MAX_GRAM,
                },
            },
            "filter": {
                "ngram": {"type": "ngram", "min_gram": 3, "max_gram": MAX_GRAM},
                "edgengram": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": MAX_GRAM,
                },
                "shallow_edgengram": {
                    "type": "edge_ngram",
                    "min_gram": 1,
                    "max_gram": MAX_GRAM,
                },
                "reversed_edgengram": {
                    "type": "edge_ngram",
                    "min_gram": 3,
                    "max_gram": MAX_GRAM,
                    "side": "back",
                },
                "max_gram_truncate": {"type": "truncate", "length": MAX_GRAM},
            },
            "char_filter": {
                "non_ascii_character_filter_mapping": {
                    "type": "mapping",
                    "mappings": ["’ => '"],
                }
            },
        },
        "index": {"number_of_shards": 1, "max_ngram_diff": MAX_GRAM},
    }


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
OSCAR_PRODUCT_SEARCH_FIELDS = SEARCH_FIELDS + ["upc^2"]
OSCAR_CATEGORY_SEARCH_FIELDS = SEARCH_FIELDS
