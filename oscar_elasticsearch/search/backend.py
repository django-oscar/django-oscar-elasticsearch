from elasticsearch import Elasticsearch

es = Elasticsearch(
    "http://127.0.0.1:9200",
    verify_certs=False,
)
