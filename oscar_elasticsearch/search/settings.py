# pylint: disable=wildcard-import,unused-wildcard-import
from django.conf import settings
from django.utils.translation import gettext_lazy as _

# from extendedsearch.settings import *
from .constants import ES_CTX_AVAILABLE, ES_CTX_PUBLIC

HANDLE_STOCKRECORD_CHANGES = getattr(
    settings, "OSCAR_ELASTICSEARCH_HANDLE_STOCKRECORD_CHANGES", True
)
MIN_NUM_BUCKETS = getattr(settings, "OSCAR_ELASTICSEARCH_MIN_NUM_BUCKETS", 2)
FILTER_AVAILABLE = getattr(settings, "OSCAR_ELASTICSEARCH_FILTER_AVAILABLE", False)
DEFAULT_ITEMS_PER_PAGE = getattr(
    settings,
    "OSCAR_ELASTICSEARCH_DEFAULT_ITEMS_PER_PAGE",
    settings.OSCAR_PRODUCTS_PER_PAGE,
)
ITEMS_PER_PAGE_CHOICES = getattr(
    settings, "OSCAR_ELASTICSEARCH_ITEMS_PER_PAGE_CHOICES", [DEFAULT_ITEMS_PER_PAGE]
)
MONTHS_TO_RUN_ANALYTICS = getattr(
    settings, "OSCAR_ELASTICSEARCH_MONTHS_TO_RUN_ANALYTICS", 3
)
SUGGESTION_STATUS_FILTER = getattr(
    settings,
    "OSCAR_ELASTICSEARCH_SUGGESTION_STATUS_FILTER",
    ES_CTX_AVAILABLE if FILTER_AVAILABLE else ES_CTX_PUBLIC,
)
FACETS = getattr(settings, "OSCAR_ELASTICSEARCH_FACETS", [])
AUTOCOMPLETE_CONTEXTS = getattr(
    settings, "OSCAR_ELASTICSEARCH_AUTOCOMPLETE_CONTEXTS", []
)

INDEX_PREFIX = getattr(
    settings, "OSCAR_ELASTICSEARCH_INDEX_PREFIX", "django-oscar-elasticsearch"
)

NUM_SUGGESTIONS = getattr(settings, "OSCAR_ELASTICSEARCH_NUM_SUGGESTIONS", 20)

ELASTICSEARCH_SERVER_URLS = getattr(
    settings, "OSCAR_ELASTICSEARCH_SERVER_URLS", ["http://127.0.0.1:9200"]
)


RELEVANCY = "relevancy"
TOP_RATED = "rating"
NEWEST = "newest"
PRICE_HIGH_TO_LOW = "price-desc"
PRICE_LOW_TO_HIGH = "price-asc"
TITLE_A_TO_Z = "title-asc"
TITLE_Z_TO_A = "title-desc"
POPULARITY = "popularity"


SORT_BY_CHOICES_SEARCH = getattr(
    settings,
    "OSCAR_ELASTICSEARCH_SORT_BY_CHOICES_SEARCH",
    [
        (RELEVANCY, _("Relevancy")),
        (POPULARITY, _("Most popular")),
        (NEWEST, _("Newest")),
    ],
)

SORT_BY_MAP_SEARCH = getattr(
    settings,
    "OSCAR_ELASTICSEARCH_SORT_BY_MAP_SEARCH",
    {NEWEST: "-date_created", POPULARITY: "-popularity"},
)

SORT_BY_CHOICES_CATALOGUE = getattr(
    settings,
    "OSCAR_ELASTICSEARCH_SORT_BY_CHOICES_CATALOGUE",
    [
        (RELEVANCY, _("Relevancy")),
        (POPULARITY, _("Most popular")),
        (TOP_RATED, _("Customer rating")),
        (NEWEST, _("Newest")),
        (PRICE_HIGH_TO_LOW, _("Price high to low")),
        (PRICE_LOW_TO_HIGH, _("Price low to high")),
        (TITLE_A_TO_Z, _("Title A to Z")),
        (TITLE_Z_TO_A, _("Title Z to A")),
    ],
)

SORT_BY_MAP_CATALOGUE = getattr(
    settings,
    "OSCAR_ELASTICSEARCH_SORT_BY_MAP_CATALOGUE",
    {
        TOP_RATED: "-rating",
        NEWEST: "-date_created",
        POPULARITY: "-popularity",
        PRICE_HIGH_TO_LOW: "-price",
        PRICE_LOW_TO_HIGH: "price",
        TITLE_A_TO_Z: "title",
        TITLE_Z_TO_A: "-title",
    },
)
