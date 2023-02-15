# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

import logging

from . import Tdb, MixinSearchById

log = logging.getLogger(__name__)


class Company(Tdb, MixinSearchById):
    """
    Model wrapper for Tryton model object 'company.company'.
    """

    __name__ = 'company.company'
