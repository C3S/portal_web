# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

"""
Helper Tests
"""

from decimal import Decimal

from ..base import UnitTestBase

from ...helpers import format_currency
from ...models import Tdb
import logging

log = logging.getLogger(__name__)


class TestHelpers(UnitTestBase):

    @classmethod
    def setUpClass(cls):
        """
        Initializes the database connection.
        """
        super(TestHelpers, cls).setUpClass()
        Tdb.init()

    @Tdb.transaction()
    def test_format_currency(self):
        """
        Does converting a decimal to a money formatted string work?
        """

        d = Decimal('-1234567.8901')
        self.assertEqual(
            format_currency(
                d, curr='$', sep=',', dp='.'
            ),
            '-$ 1,234,567.89'
        )
        self.assertEqual(
            format_currency(
                d, curr='$', sep=',', dp='.', neg='(', trailneg=')'
            ),
            '($ 1,234,567.89)'
        )
