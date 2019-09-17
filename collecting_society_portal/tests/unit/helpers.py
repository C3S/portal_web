# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

"""
Helper Tests
"""

from decimal import Decimal

from ..base import UnitTestBase

from ...helpers import format_currency
from ...models import Tdb
import logging

from trytond.transaction import Transaction
from trytond.cache import Cache
from trytond.pool import Pool

log = logging.getLogger(__name__)


class TestHelpers(UnitTestBase):

    @classmethod
    def setUpClass(cls):
        """
        Sets up test unit class.

        Establishes a db connection and starts a transaction.

        Returns:
            None.
        """

        Tdb._db = "test"
        Tdb._user = 0
        Tdb._configfile = "/ado/etc/trytond_test_postgres.conf"
        Tdb._company = 1
        Tdb.init()

        user = Transaction().user  # pyramid subrequests have no cursor
        cursor = Transaction().cursor and not Transaction().cursor._conn.closed
        # import ptvsd
        # ptvsd.enable_attach(address=("0.0.0.0", 51003),
        #                     redirect_output=True)
        # ptvsd.wait_for_attach()
        # ptvsd.break_into_debugger()
        if not user and not cursor:
            with Transaction().start(Tdb._db, 0):
                pool = Pool(str(Tdb._db))
                user = pool.get('res.user')
                context = user.get_preferences(context_only=True)
                Cache.clean(Tdb._db)
            Transaction().start(
                Tdb._db, Tdb._user, readonly=True, context=context)

    @classmethod
    def tearDownClass(cls):
        """
        Tears down unit test class.

        Closes db.

        Returns:
            None.
        """
        cursor = Transaction().cursor
        if cursor and not Transaction().cursor._conn.closed:
             Cache.resets(Tdb._db)
            # import ptvsd
            # ptvsd.enable_attach(address=("0.0.0.0", 51003),
            #                     redirect_output=True)
            # ptvsd.wait_for_attach()
            # ptvsd.break_into_debugger()
            Transaction().stop()

    def setUp(self):
        pass

    @Tdb.transaction()
    def test_format_currency(self):
        '''
        Does converting a decimal to a money formatted string work?
        '''

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
