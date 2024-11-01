from oscar.core.loading import get_class

OscarResource = get_class("oscar_odin.resources.base", "OscarResource")


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
