# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

"""
Helper functions included as top-level names in temlating system.
"""

__all__ = [
    'b64encode',
    'environ',
    'log',
    'format_currency'
]

from os import environ
from decimal import Decimal
import logging
from base64 import b64encode

from .models import (
    Tdb,
    Company
)

environ = dict(environ)
log = logging.getLogger(__name__)


@Tdb.transaction()
def format_currency(value, places=None, curr=None, sep=None, dp=None, pos=None,
                    neg=None, trailneg=None):
    """
    Convert Decimal to a money formatted string.

    Defaults to currency of tryton company.

    Args:
        places:  required number of places after the decimal point
        curr:    optional currency symbol before the sign (may be blank)
        sep:     optional grouping separator (comma, period, space, or blank)
        dp:      decimal point indicator (comma or period)
                 only specify as blank when places is zero
        pos:     optional sign for positive numbers: '+', space or blank
        neg:     optional sign for negative numbers: '-', '(', space or blank
        trailneg:optional trailing minus indicator:  '-', ')', space or blank

    Returns:
        str: Formatted money value.

    Examples:
        >>> d = Decimal('-1234567.8901')
        >>> format_currency(d, curr='$')
        '-$1,234,567.89'
        >>> format_currency(d, places=0, sep='.', dp='', neg='', trailneg='-')
        '1.234.568-'
        >>> format_currency(d, curr='$', neg='(', trailneg=')')
        '($1,234,567.89)'
        >>> format_currency(Decimal(123456789), sep=' ')
        '123 456 789.00'
        >>> format_currency(Decimal('-0.02'), neg='<', trailneg='>')
        '<0.02>'
    """
    currency = Company.search_by_id(Tdb._company).currency

    _places = places or currency.digits
    _curr = curr or currency.symbol
    _sep = sep or "."
    _dp = dp or ","
    _pos = pos or "+"
    _neg = neg or "-"
    _trailneg = trailneg or ''

    q = Decimal(10) ** -_places
    sign, digits, exp = value.quantize(q).as_tuple()
    result = []
    digits = list(map(str, digits))
    build, next = result.append, digits.pop
    if sign:
        build(_trailneg)
    for i in range(_places):
        build(next() if digits else '0')
    build(_dp)
    if not digits:
        build('0')
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(_sep)
    build(' ')
    build(_curr)
    build(_neg if sign else _pos)
    return ''.join(reversed(result))
