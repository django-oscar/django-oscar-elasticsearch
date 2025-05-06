from collections import defaultdict

from django.db import connection
from django.db.models import Case, When


def chunked(iterable, size, startindex=0):
    """
    Divide an interable into chunks of ``size``

    >>> list(chunked("hahahaha", 2))
    ['ha', 'ha', 'ha', 'ha']
    >>> list(chunked([1,2,3,4,5,6,7], 3))
    [[1, 2, 3], [4, 5, 6], [7]]
    """
    while True:
        chunk = iterable[startindex : startindex + size]
        chunklen = len(chunk)
        if chunklen:
            yield chunk
        if chunklen < size:
            break
        startindex += size


def search_result_to_queryset(search_results, Model):
    instance_ids = [hit["_source"]["id"] for hit in search_results["hits"]["hits"]]

    preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(instance_ids)])
    return Model.objects.filter(pk__in=instance_ids).order_by(preserved)


def get_index_settings(MAX_GRAM):
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


def get_category_ancestors():
    """
    Get a mapping of all child categories with all of its ancestor categories.
    {child_id: [ancestor1_id, ancestor2_id]}}
    """
    query = """
        SELECT 
            child.id AS child_id,
            parent.id AS up_id
        FROM catalogue_category AS child
        JOIN catalogue_category AS parent
        ON child.path LIKE (parent.path || '%') AND child.id > parent.id;
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    category_ancestors = defaultdict(list)
    for child_id, ancestor_id in rows:
        category_ancestors[child_id].append(ancestor_id)

    return category_ancestors
