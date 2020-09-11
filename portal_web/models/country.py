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

class Subdivision(Tdb, MixinSearchById, MixinSearchByCode, MixinSearchByName,
              MixinSearchAll):
    """
    Model wrapper for Tryton model object 'country.subdivision'.
    """

    __name__ = 'country.subdivision'
