# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

import logging

from . import (
    Tdb,
    MixinSearchById,
    MixinSearchByCode,
    MixinSearchByName,
    MixinSearchAll
)

log = logging.getLogger(__name__)


class Country(Tdb, MixinSearchById, MixinSearchByCode, MixinSearchByName,
              MixinSearchAll):
    """
    Model wrapper for Tryton model object 'country.country'.
    """

    __name__ = 'country.country'

    @classmethod
    def search_all(cls, active=True):
        """
        Fetches all Countries

        Returns:
          list: country
          None: if no match is found
        """
        return cls.get().search([('active', 'in', (True, active))])

    @classmethod
    def search_by_code(cls, country_code, active=True):
        """
        Searches an country by country code

        Args:
          country_code (string): country.code

        Returns:
          obj: country
          None: if no match is found
        """
        result = cls.get().search([
            ('code', '=', country_code),
            ('active', 'in', (True, active))
        ])
        if not result:
            return None
        return result[0]


class Subdivision(Tdb, MixinSearchById, MixinSearchByCode, MixinSearchByName,
                  MixinSearchAll):
    """
    Model wrapper for Tryton model object 'country.subdivision'.
    """

    __name__ = 'country.subdivision'
