import re
import decimal
from oscar.templatetags.currency_filters import currency as currency_filter

RANGE_REGEX = re.compile(r"(?P<first>[\d\*\.]+)-(?P<second>[\d\*\.]+)")


def currency(key):
    """
    Formatter for facet keys as currency

    >>> currency("*-25.0")
    '€\xa025,00'
    >>> currency("25.0-*")
    '€\xa025,00'
    >>> currency("25.0-23")
    '€\xa025,00 - €\xa023,00'

    """
    parsed_key = RANGE_REGEX.match(key)
    if parsed_key is not None:
        first = parsed_key.group("first")
        second = parsed_key.group("second")
    if first == "*":
        return currency_filter(second)
    elif second == "*":
        return currency_filter(first)
    else:
        return "%s - %s" % (currency_filter(first), currency_filter(second))

    return currency(0)


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
    try:
        return int(decimal.Decimal(key).to_integral_value(decimal.ROUND_HALF_UP))
    except decimal.InvalidOperation:
        return 0


def decimal1(key):
    """
    >>> str(decimal1(0.876876876))
    '0.9'
    """
    return decimal.Decimal(key).quantize(decimal.Decimal("0.1"), decimal.ROUND_HALF_UP)


def decimal2(key):
    """
    >>> str(decimal2(0.876876876))
    '0.88'
    """
    return decimal.Decimal(key).quantize(decimal.Decimal("0.01"), decimal.ROUND_HALF_UP)


def decimal3(key):
    """
    >>> str(decimal3(0.876876876))
    '0.877'
    """
    return decimal.Decimal(key).quantize(
        decimal.Decimal("0.001"), decimal.ROUND_HALF_UP
    )
