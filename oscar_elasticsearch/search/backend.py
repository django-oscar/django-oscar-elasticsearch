from elasticsearch import Elasticsearch

from oscar_elasticsearch.search.settings import ELASTICSEARCH_SERVER_URLS

es = Elasticsearch(
    hosts=ELASTICSEARCH_SERVER_URLS,
    verify_certs=False,
)
