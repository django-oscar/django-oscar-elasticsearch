import functools
import re
import decimal
from django.utils.translation import gettext_lazy as _
from oscar.templatetags.currency_filters import currency as currency_filter

RANGE_REGEX = re.compile(r"(?P<first>[\d\*\.]+)-(?P<second>[\d\*\.]+)")


def ranged(
    format_full=_("%(first)s - %(second)s"),
    format_first=_("%(first)s or more"),
    format_second=_("Up to %(second)s"),
):
    """Decorator for formatter functions to handle ranged data"""

    if callable(format_full):
        raise RuntimeError('Factory-only decorator. Use "@ranged()".')

    def wrap(func):
        @functools.wraps(func)
        def inner(key):
            parsed_key = RANGE_REGEX.match(str(key))
            if parsed_key is None:
                return func(key)

            first = parsed_key.group("first")
            second = parsed_key.group("second")

            if first == "*":
                return format_second % {"second": func(second)}
            elif second == "*":
                return format_first % {"first": func(first)}
            else:
                return format_full % {"first": func(first), "second": func(second)}

        return inner

    return wrap


@ranged()
def currency(key):
    """
    Formatter for facet keys as currency

    >>> currency("*-25.0")
    'Up to €25.00'
    >>> currency("25.0-*")
    '€25.00 or more'
    >>> currency("25.0-23")
    '€25.00 - €23.00'

    """
    return currency_filter(key)


def to_int(value):
    try:
        return int(decimal.Decimal(value).to_integral_value(decimal.ROUND_HALF_UP))
    except decimal.InvalidOperation:
        return 0


@ranged()
def integer(key):
    """
    >>> integer("687987.8778.8978")
    0
    >>> integer("henk")
    0
    >>> integer("-5656.89889")
    -5657
    >>> integer("345.876867")
    346
    """
    return to_int(key)


@ranged()
def integer_ml(key):
    """
    >>> integer_ml("687987.8778.8978")
    '0 ml'
    >>> integer_ml("henk")
    '0 ml'
    >>> integer_ml("-5656.89889")
    '-5657 ml'
    >>> integer_ml("345.876867")
    '346 ml'
    """
    value = to_int(key)
    return f"{value} ml"


@ranged()
def decimal1(key):
    """
    >>> str(decimal1(0.876876876))
    '0.9'
    """
    return decimal.Decimal(key).quantize(decimal.Decimal("0.1"), decimal.ROUND_HALF_UP)


@ranged()
def decimal2(key):
    """
    >>> str(decimal2(0.876876876))
    '0.88'
    """
    return decimal.Decimal(key).quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP)


@ranged()
def decimal3(key):
    """
    >>> str(decimal3(0.876876876))
    '0.877'
    """
    return decimal.Decimal(key).quantize(
        decimal.Decimal("0.001"), decimal.ROUND_HALF_UP
    )
