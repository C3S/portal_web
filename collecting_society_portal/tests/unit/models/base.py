# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

from ...base import UnitTestBase

from trytond.pool import Pool
from ....models import Tdb


class TestTdb(UnitTestBase):

    def test_is_pool_a_pool_object(self):
        """
        Is pool a Pool object?
        """
        pool = Tdb.pool()
        assert isinstance(pool, Pool)
