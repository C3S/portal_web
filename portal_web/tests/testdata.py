# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

from ..models import Tdb, WebUser, Party, WebUserRole


class TestDataPortal():
    """
    Mix-in class for portal with helper functions to create test data.
    """

    @classmethod
    @Tdb.transaction(readonly=False)
    def createWebUser(cls, email, password, role=False,
                      opt_in_state='opted-in'):
        if role:
            roles = [WebUserRole.search_by_code(role).id]
        else:
            roles = [r.id for r in WebUserRole.search_all()]
        webuser, = WebUser.create([{
            'email': email,
            'password': password,
            'roles': [('add', roles)],
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
