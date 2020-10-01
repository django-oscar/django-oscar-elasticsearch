from django.db import models
from django.utils.functional import lazy

from oscar.core.loading import get_model

# pylint: disable=unused-import
from extendedsearch.utils import merge_dicts, unique_everseen

from . import settings

ProductAttribute = get_model("catalogue", "ProductAttribute")


def _product_attributes_es_config():
    props = {}
    for attribute in ProductAttribute.objects.exclude(
        models.Q(code="") | models.Q(code__isnull=True)
    ):
        es_type = es_type_for_product_attribute(attribute)
        code = attribute.code
        if es_type != "text":
            if code in props:
                if (
                    props[code]["type"] != es_type
                ):  # use keyword if different types are detected
                    props[code] = {"type": "keyword"}
            else:
                props[code] = {"type": es_type}

    return {"type": "object", "properties": props}


product_attributes_es_config = lazy(_product_attributes_es_config, dict)


def es_type_for_product_attribute(attribute):
    if attribute.type == attribute.TEXT:
        return "keyword"
    elif attribute.type == attribute.RICHTEXT:
        return "text"
    elif attribute.type == attribute.DATE:
        return "date"
    elif attribute.type == attribute.DATETIME:
        return "date"
    elif attribute.type == attribute.BOOLEAN:
        return "boolean"
    elif attribute.type == attribute.INTEGER:
        return "integer"
    elif attribute.type == attribute.INTEGER:
        return "integer"
    elif attribute.type == attribute.FLOAT:
        return "float"
    elif attribute.type == attribute.OPTION:
        return "keyword"
    elif attribute.type == attribute.MULTI_OPTION:
        return "keyword"
    else:
        return "text"


def get_facet_names():
    return [facet["name"] for facet in settings.FACETS]


def chunked(qs, size, startindex=0):
    """
    Divide an interable into chunks of ``size``

    >>> list(chunked("hahahaha", 2))
    ['ha', 'ha', 'ha', 'ha']
    >>> list(chunked([1,2,3,4,5,6,7], 3))
    [[1, 2, 3], [4, 5, 6], [7]]
    """
    while True:
        chunk = qs[startindex : startindex + size]
        chunklen = len(chunk)
        if chunklen:
            yield chunk
        if chunklen < size:
            break
        startindex += size
