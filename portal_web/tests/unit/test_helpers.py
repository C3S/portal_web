# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

"""
Helper Tests
"""

from decimal import Decimal

import pytest

from ...helpers import format_currency


@pytest.mark.usefixtures('tryton')
class TestHelpers:
    """
    Helper test class
    """
    def test_format_currency(self):
        """
        Format a decimal as currency
        """
        decimal = Decimal('-1234567.8901')

        currency = format_currency(decimal, curr='$', sep=',', dp='.')
        assert currency == '-$ 1,234,567.89'

        currency = format_currency(
            decimal, curr='$', sep=',', dp='.', neg='(', trailneg=')')
        assert currency == '($ 1,234,567.89)'
