from extendedsearch import index
from .constants import APP_LABEL


class ProductProxyMixinMeta:
    """
    This is so we can extend the search app and add 
    methods to the ProductProxy without replacing the entire app.
    If the ProductProxyMixin has no _meta attribute the field name can not
    be determined by wagtail.
    """

    app_label = APP_LABEL
    abstract = True
    swapped = False
    local_managers = []


class ProductProxyMixin(index.Indexed):
    _meta = ProductProxyMixinMeta()

    def process_attributes(self, attrs):
        return attrs

    search_fields = []
