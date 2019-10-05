# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

import logging

from . import Tdb

log = logging.getLogger(__name__)


class Company(Tdb):
    """
    Model wrapper for Tryton model object 'company.company'.
    """

    __name__ = 'company.company'

    @classmethod
    def search_by_id(cls, company_id):
        """
        Searches a company by company id.

        Args:
            company_id (int): Company id.

        Returns:
            obj: Company.
            None: if no match is found.
        """
        result = cls.get().search([('id', '=', company_id)])
        return result[0] or None
