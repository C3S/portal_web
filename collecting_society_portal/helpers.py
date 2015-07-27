# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import logging
from base64 import b64encode
from decimal import Decimal

from collecting_society_portal.models import (
    Tdb,
    Company
)

log = logging.getLogger(__name__)


@Tdb.transaction(readonly=True)
def format_currency(value, places=None, curr=None, sep=None, dp=None, pos=None,
                    neg=None, trailneg=None):
    """
    Convert Decimal to a money formatted string.

    Defaults to currency of tryton company.

    places:  required number of places after the decimal point
    curr:    optional currency symbol before the sign (may be blank)
    sep:     optional grouping separator (comma, period, space, or blank)
    dp:      decimal point indicator (comma or period)
             only specify as blank when places is zero
    pos:     optional sign for positive numbers: '+', space or blank
    neg:     optional sign for negative numbers: '-', '(', space or blank
    trailneg:optional trailing minus indicator:  '-', ')', space or blank

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
    # context = Tdb.context()
    currency = Company.search_by_id(Tdb._company).currency

    _places = places or currency.digits
    _curr = curr or currency.symbol
    _sep = sep or currency.mon_thousands_sep
    _dp = dp or currency.mon_decimal_point
    _pos = pos or currency.positive_sign
    _neg = neg or currency.negative_sign
    _trailneg = trailneg or currency.n_cs_precedes

    q = Decimal(10) ** -_places      # 2 _places --> '0.01'
    sign, digits, exp = value.quantize(q).as_tuple()
    result = []
    digits = map(str, digits)
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
