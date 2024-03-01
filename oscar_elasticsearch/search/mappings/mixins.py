import odin

from datetime import datetime


class OscarElasticSearchResourceMixin(odin.AnnotatedResource):
    id: str
    content_type: str
    title: str
    is_public: bool
    code: str
    description: str
    absolute_url: str
    slug: str
