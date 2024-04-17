import odin

from oscar_odin.resources._base import OscarResource

from datetime import datetime


class OscarElasticSearchResourceMixin(OscarResource):
    id: str
    content_type: str
    title: str
    is_public: bool
    code: str
    description: str
    absolute_url: str
    slug: str
