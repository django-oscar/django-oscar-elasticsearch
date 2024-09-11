from decimal import Decimal

from typing import Optional, List

from datetime import datetime

from oscar_odin.resources._base import OscarResource
from oscar_odin.fields import DecimalField

from oscar_elasticsearch.search.mappings.mixins import OscarElasticSearchResourceMixin


class CategoryElasticSearchRelatedResource(OscarResource):
    id: int
    description: str
    full_name: str


class ProductElasticSearchResource(OscarElasticSearchResourceMixin):
    upc: str
    title_auto_complete: str
    code_auto_complete: str
    structure: str
    rating: Optional[float]
    priority: int
    parent_id: Optional[int]
    product_class: Optional[int]
    price: Decimal = DecimalField()
    currency: str
    num_available: int
    is_available: bool
    categories: List[CategoryElasticSearchRelatedResource]
    attrs: dict
    date_created: datetime
    date_updated: datetime
    string_attrs: List[str]
    popularity: int
    status: List[str]
    suggest: List[str]
