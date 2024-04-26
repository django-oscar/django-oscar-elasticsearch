from oscar_odin.resources._base import OscarResource


class OscarElasticSearchResourceMixin(OscarResource):
    id: str
    content_type: str
    title: str
    is_public: bool
    code: str
    description: str
    absolute_url: str
    slug: str
    search_title: str
