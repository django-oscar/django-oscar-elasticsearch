from django.db import models
from django.conf import settings
from django.utils.functional import lazy

from oscar.core.loading import get_model

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


def get_facet_table():
    return {facet["name"]: facet for facet in settings.OSCAR_SEARCH.get("FACETS")}


def get_facet_names():
    return [facet["name"] for facet in settings.OSCAR_SEARCH.get("FACETS")]


def to_float(num):
    try:
        return float(num)
    except ValueError:
        return 0


def merge_dicts(target, updates, overwrite=False, multivalue=False):
    """
    Merge two dicts

    >>> first = {'a': 1, 'b': [1], 'c': {'d': 1, 'e': [2]}}
    >>> second = {'a': 3, 'b': 'hanny', 'c': {'d': 9, 'e': [7], 'f': [99]}, 'g': 8}
    >>> merge_dicts(first, second)
    {'a': 1, 'b': [1, 'hanny'], 'c': {'d': 1, 'e': [2, 7], 'f': [99]}, 'g': 8}
    >>> first = {'a': 1, 'b': [1], 'c': {'d': 1, 'e': [2]}}
    >>> merge_dicts(first, second, multivalue=True)
    {'a': [1, 3], 'b': [1, 'hanny'], 'c': {'d': 1, 'e': [2, 7], 'f': [99]}, 'g': 8}
    >>> first = {'a': 1, 'b': [1], 'c': {'d': 1, 'e': [2]}}
    >>> merge_dicts(first, second, overwrite=True)
    {'a': 3, 'b': [1, 'hanny'], 'c': {'d': 9, 'e': [2, 7], 'f': [99]}, 'g': 8}
    """
    for key, value in updates.items():
        if key in target:
            item = target[key]
            if isinstance(item, dict):
                if isinstance(value, Mapping):
                    target[key] = merge_dicts(item, value, overwrite)
                elif overwrite:
                    target[key] = value
                else:
                    raise Exception("can not merge nub")
            elif isinstance(item, list):
                if isinstance(value, str):
                    item.append(value)
                elif isinstance(value, Iterable):
                    item += list(value)
                else:
                    item.append(value)
            elif multivalue and value != item:  # gather multiple values into list
                target[key] = [item, value]
            elif overwrite:
                target[key] = value
        else:
            target[key] = value

    return target


def unique_everseen(iterable, key=None):
    """List unique elements, preserving order. Remember all elements ever seen.

    >>> list(unique_everseen('AAAABBBCCDAABBB'))
    ['A', 'B', 'C', 'D']
    >>> list(unique_everseen('ABBCcAD', str.lower))
    ['A', 'B', 'C', 'D']
    """
    seen = set()
    seen_add = seen.add
    if key is None:
        for element in filterfalse(seen.__contains__, iterable):
            seen_add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen_add(k)
                yield element
