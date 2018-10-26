# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import logging

from . import Tdb

log = logging.getLogger(__name__)


class WebUserRole(Tdb):
    """
    Model wrapper for Tryton model object 'web.user.role'.
    """

    __name__ = 'web.user.role'

    @classmethod
    def search_all(cls):
        """
        Gets all web user roles.

        Returns:
            list (obj[web.user.role]): List of web user roles.
            None: if no match is found.
        """
        return cls.get().search([])

    @classmethod
    def search_by_code(cls, code):
        """
        Searches a web user role by code.

        Args:
            code (string): Code of the web user role.

        Returns:
            obj (web.user): Web user role.
            None: If no match is found.
        """
        if code is None:
            return None
        result = cls.get().search([('code', '=', code)])
        return result[0] if result else None
