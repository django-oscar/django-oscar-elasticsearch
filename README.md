# Django Oscar Elasticsearch

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Version](https://img.shields.io/badge/version-2.0.0-green)

## 🚀 Major Overhaul Update!

The latest version (3.0.0) includes a complete overhaul with significant updates to the codebase, new features, and performance enhancements.

## 📖 About

Django Oscar Elasticsearch is a search app that integrates Elasticsearch with the Django Oscar framework for improved search functionality.

## 🆕 What's New

- **New Elasticsearch Integration**: Enhanced search capabilities using Elasticsearch. We removed wagtail from the dependencies and created our own API.
- **Improved Performance**: Faster and more efficient search operations.
- **Breaking Changes**: Configuration changes may require updates to existing Oscar settings. Also search handlers are removed in djang-oscar==3.2.5

## 📦 Installation

Follow these steps to set up the project:

1. Install the package:
    ```bash
    pip install django-oscar-elasticsearch
    ```
2. Update your `INSTALLED_APPS` in Django settings:
    ```python
    INSTALLED_APPS = [
        ...
        "oscar_elasticsearch.search.apps.OscarElasticSearchConfig",
        "widget_tweaks",
    ]
    ```
3. Configure the necessary settings as outlined in the project documentation.

## 🛠 Configuration

- **`OSCAR_ELASTICSEARCH_HANDLE_STOCKRECORD_CHANGES`**: Enables handling of stock record changes automatically. Default is `True`.
- **`OSCAR_ELASTICSEARCH_MIN_NUM_BUCKETS`**: Minimum number of buckets for search facets. Default is `2`.
- **`OSCAR_ELASTICSEARCH_FILTER_AVAILABLE`**: Filters products based on availability status. Default is `False`.
- **`OSCAR_ELASTICSEARCH_DEFAULT_ITEMS_PER_PAGE`**: Number of items displayed per page. Defaults to `OSCAR_PRODUCTS_PER_PAGE`.
- **`OSCAR_ELASTICSEARCH_ITEMS_PER_PAGE_CHOICES`**: Options for items per page settings. Default is `[DEFAULT_ITEMS_PER_PAGE]`.
- **`OSCAR_ELASTICSEARCH_MONTHS_TO_RUN_ANALYTICS`**: Defines months to run analytics queries. Default is `3`.
- **`OSCAR_ELASTICSEARCH_FACETS`**: Customizable search facets for filtering.
- **`OSCAR_ELASTICSEARCH_SUGGESTION_STATUS_FILTER`**: Status filter for search suggestions, default depends on availability settings.
- **`OSCAR_ELASTICSEARCH_SUGGESTION_FIELD_NAME`**: Field name used for suggestions. Default is `"search_title"`.
- **`OSCAR_ELASTICSEARCH_AUTOCOMPLETE_CONTEXTS`**: Contexts for autocomplete suggestions.
- **`OSCAR_ELASTICSEARCH_AUTOCOMPLETE_SEARCH_FIELDS`**: Fields used in autocomplete search. Default is `["title", "upc"]`.
- **`OSCAR_ELASTICSEARCH_SEARCH_FIELDS`**: Specifies fields used for general search queries.
- **`OSCAR_ELASTICSEARCH_SEARCH_QUERY_TYPE`**: Type of query used in search; default is `"most_fields"`.
- **`OSCAR_ELASTICSEARCH_SEARCH_QUERY_OPERATOR`**: Logical operator for search queries. Default is `"or"`.
- **`OSCAR_ELASTICSEARCH_NUM_SUGGESTIONS`**: Maximum number of suggestions returned. Default is `20`.
- **`OSCAR_ELASTICSEARCH_SERVER_URLS`**: Elasticsearch server URLs. Default is `["http://127.0.0.1:9200"]`.
- **`OSCAR_ELASTICSEARCH_INDEX_PREFIX`**: Prefix used for Elasticsearch indices. Default is `"django-oscar-elasticsearch"`.
- **`OSCAR_ELASTICSEARCH_SORT_BY_CHOICES_SEARCH`**: Sorting options for search results.
- **`OSCAR_ELASTICSEARCH_SORT_BY_MAP_SEARCH`**: Maps sort options to actual query parameters.
- **`OSCAR_ELASTICSEARCH_SORT_BY_CHOICES_CATALOGUE`**: Sorting options specific to the catalog view.
- **`OSCAR_ELASTICSEARCH_SORT_BY_MAP_CATALOGUE`**: Maps catalog sort options to query parameters.
- **`OSCAR_ELASTICSEARCH_DEFAULT_ORDERING`**: Default ordering setting for searches.
- **`OSCAR_ELASTICSEARCH_FACET_BUCKET_SIZE`**: Sets the size of facet buckets. Default is `10`.
- **`OSCAR_ELASTICSEARCH_INDEXING_CHUNK_SIZE`**: Defines chunk size for batch indexing operations. Default is `400`.
- **`OSCAR_ELASTICSEARCH_PRIORITIZE_AVAILABLE_PRODUCTS`**: Prioritizes available products in search results. Default is `True`.


## 📜 Usage

Django Oscar Elasticsearch is designed primarily to index products and categories from Django Oscar, but it can also index any Django model or external data types, such as CSV or Excel files.

### Indexing Django Models
You can configure custom search handlers to index any Django model. Define a search document, map the fields you want to index, and create a corresponding search handler.

Create the index definition
```python
from django.contrib.auth import get_user_model

from oscar.core.loading import get_class, get_model

get_oscar_index_settings = get_class(
    "search.indexing.settings", "get_oscar_index_settings"
)

OSCAR_INDEX_SETTINGS = get_oscar_index_settings()

BaseElasticSearchApi = get_class("search.api.search", "BaseElasticSearchApi")
ESModelIndexer = get_class("search.indexing.indexer", "ESModelIndexer")


class UserElasticsearchIndex(BaseElasticSearchApi, ESModelIndexer):
    INDEX_NAME = "users"
    INDEX_MAPPING = {
        "properties": {
            "id": {"type": "integer", "store": True},
            "full_name": {"type": "text"},
            "is_active": {"type": "boolean"}
        }
    }
    INDEX_SETTINGS = OSCAR_INDEX_SETTINGS
    Model = get_user_model()

    def make_documents(self, objects):
        for user in objects:
            yield {"_id": user.id, "_source": {"id": user.id, "full_name": user.get_full_name(), "is_active": user.is_active}}
```

Indexing users into elasticsearch, this can be done in a management command for example
```python
from django.contrib.auth import get_user_model
from oscar_elasticsearch.search import settings

from myprojects.usersearch import UserElasticsearchIndex

User = get_user_model()


with UserElasticsearchIndex().reindex() as index:
    for chunk in chunked(users, settings.INDEXING_CHUNK_SIZE):
        index.reindex_objects(chunk)
```

Searching for users on full_name
```python
from myprojects.usersearch import UserElasticsearchIndex

# non paginated, returns a queryset of selected model
users = UserElasticsearchIndex().search(
    from_=0,
    to=10,
    query_string="henk",
    search_fields=["full_name^1.5"],
    filters={"term": {"is_active_": True}}, # only active users
)

# paginated, returns a paginator object that extends from the django paginator
paginator = UserElasticsearchIndex().paginated_search(
    from_=0,
    to=10,
    query_string="henk",
    search_fields=["full_name^1.5"],
    filters={"term": {"is_active_": True}}, # only active users
)
```

## 🤝 Contributing

Contributions are welcome! Please submit issues and pull requests to the repository.

## 📄 License

Oscar is released under the permissive [New BSD license](https://github.com/django-oscar/django-oscar-elasticsearch/blob/master/LICENSE) ([see summary](https://tldrlegal.com/license/bsd-3-clause-license-(revised))).

## 📫 Contact

For questions or support, please contact the maintainers via GitHub issues.
