# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

from ...base import UnitTestBase

from trytond.pool import Pool
from ....models import Tdb, WebUser


class TestTdb(UnitTestBase):

    def setUp(self):
        Tdb._db = "test"
        Tdb._user = 0
        Tdb._configfile = "/ado/etc/trytond.conf"
        Tdb._company = 1
        Tdb.init()

    def test_is_pool_a_pool_object(self):
        """
        Is pool a Pool object?
        """

        pool = Tdb.pool()
        assert isinstance(pool, Pool)

    @Tdb.transaction()
    def test_autenticate_user(self):
        """
        Can standard user be authenticated?
        """

        webu = WebUser.authenticate("alf_imp@c3s.cc", "cc")
        assert (webu is not None)

    @Tdb.transaction()
    def test_autenticate_wrong_user(self):
        """
        Does wrong authentication throw an error?
        """

        webu = WebUser.authenticate("alf_pimp@c3s.cc", "cc")
        assert (webu is None)
