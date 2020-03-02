# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

from ..models import Tdb, WebUser, Party, WebUserRole


class TestDataPortal():
    """
    Mix-in class for portal with helper functions to create test data.
    """

    @classmethod
    @Tdb.transaction(readonly=False)
    def createWebUser(cls, email, password, role='licenser',
                      opt_in_state='opted-in'):
        webuser, = WebUser.create([{
            'email': email,
            'password': password,
            'roles': [('add', [WebUserRole.search_by_code(role).id])],
            'opt_in_state': opt_in_state
        }])
        cls.data.append(webuser)
        return webuser

    @classmethod
    @Tdb.transaction(readonly=False)
    def createParty(cls, name, firstname='', lastname=''):
        party, = Party.create([{
            'name': name,
            'firstname': firstname,
            'lastname': lastname
        }])
        cls.data.append(party)
        return party
