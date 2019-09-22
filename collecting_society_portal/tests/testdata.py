# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

from ..models import Tdb, WebUser, WebUserRole


class TestDataPortal():
    """
    Mix-in class for portal with helper functions to create test data.
    """

    @classmethod
    @Tdb.transaction(readonly=False)
    def createWebUser(cls, email, password, opt_in_state='opted-in'):
        cls.data += WebUser.create([{
            'email': email,
            'password': password,
            'roles': [('add', [WebUserRole.search_by_code('licenser').id])],
            'opt_in_state': opt_in_state
        }])
