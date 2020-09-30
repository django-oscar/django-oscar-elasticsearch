Search app for oscar using elasticsearch
========================================

Setup
-----

The following apps need to be added to ``INSTALLED_APPS``.

```Python
INSTALLED_APPS = [
    ...
] + get_core_apps([
    "oscar_elasticsearch.search", # replace standard oscar app
]) + [
    "widget_tweaks",
    "wagtail.core",
    "wagtail.search",
]
```

Settings required to replace the search app.

```Python
OSCAR_PRODUCT_SEARCH_HANDLER = "oscar_elasticsearch.search.search_handlers.ProductSearchHandler"
OSCAR_ELASTICSEARCH_FACETS = [
    {
        "name": "price",
        "label": "Price",
        "type": "range",
        "formatter": "oscar_elasticsearch.search.format.currency",
        "ranges": [
            25,
            100,
            500,
            1000
        ]
    },
    {
        "name": "attrs.gewicht",
        "label": "Gewicht",
        "type": "term",
        "ranges": []
    },
    {
        "name": "attrs.googleshopping",
        "label": "Google product",
        "type": "term",
        "ranges": []
    },
    {
        "name": "attrs.size",
        "label": "Maat",
        "type": "term",
        "ranges": []
    },
    {
        "name": "attrs.height",
        "label": "Hoogte",
        "type": "term",
        "ranges": []
    },
    {
        "name": "attrs.zult",
        "label": "Datum",
        "type": "term",
        "ranges": []
    },
    {
        "name": "attrs.stroomverbruik",
        "label": "Stroomverbruik",
        "type": "term",
        "ranges": []
    },
    {
        "name": "attrs.bijzonderheden",
        "label": "Bijzonderheden",
        "type": "term",
        "ranges": []
    }
]

WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "oscar_elasticsearch.search.search",
        "URLS": ["http://127.0.0.1:9200"],
        "INDEX": "my-index-name",
        "TIMEOUT": 120,
        "OPTIONS": {},
        "INDEX_SETTINGS": {},
        "ATOMIC_REBUILD": True,
        "AUTO_UPDATE": True,
    }
}

HAYSTACK_CONNECTIONS = {"default": {}}
```

Finally, add your own base.html, and make sure this is in.

```
{% extends "oscar/base.html" %}

{% block scripts %}
{{ block.super }}
{{ search_form.media }}
<script>
    $('#id_q').autocomplete('{% url "search:autocomplete" %}');
</script>
{% endblock %}
```

Optionally, for a more beautiful results templates; modify your ``TEMPLATES`` to include the main Oscar Elasticsearch template dir ``OSCAR_ES_MAIN_TEMPLATE_DIR``.

```Python

from oscar import OSCAR_MAIN_TEMPLATE_DIR
from oscar_elasticsearch import OSCAR_ES_MAIN_TEMPLATE_DIR


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            OSCAR_ES_MAIN_TEMPLATE_DIR, # Optional, but make sure this is above Oscar's templates dir
            OSCAR_MAIN_TEMPLATE_DIR
        ],
        ...
    }
]
```
