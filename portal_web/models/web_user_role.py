# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

import logging

from . import Tdb, MixinSearchByCode

log = logging.getLogger(__name__)


class WebUserRole(Tdb):
    """
    Model wrapper for Tryton model object 'web.user.role'.
    """

    __name__ = 'web.user.role'

    @classmethod
    def search_all(cls, MixinSearchByCode):
        """
        Gets all web user roles.

        Returns:
            list (obj[web.user.role]): List of web user roles.
            None: if no match is found.
        """
        return cls.get().search([])
