# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

import logging

from . import Tdb, MixinSearchByName

log = logging.getLogger(__name__)


class Address(Tdb, MixinSearchByName):
    """
    Model wrapper for Tryton model object 'party.address'.
    """

    __name__ = 'party.address'

    @classmethod
    def search_all(cls):
        """
        Gets all parties.

        Returns:
            list (obj[party.address]): List of parties.
            None: if no match is found.
        """
        return cls.get().search([])

    @classmethod
    def search_by_id(cls, uid):
        """
        Searches a address by id.

        Args:
            uid (string): Id of the address.

        Returns:
            obj (party.address): Address.
            None: If no match is found.
        """
        if uid is None:
            return None
        result = cls.get().search([('id', '=', uid)])
        return result[0] if result else None

    @classmethod
    def create(cls, vlist):
        """
        Creates parties.

        Args:
            vlist (list): List of dictionaries with attributes of a address.
                [
                    {
                        'name': str (required),
                        ...
                    },
                    {
                        ...
                    }
                ]

        Returns:
            list (obj[party.address]): List of created parties.
            None: If no object was created.

        Raises:
            KeyError: If required field is missing.
        """
        for values in vlist:
            if 'name' not in values:
                raise KeyError('name is missing')
        log.debug('create address:\n{}'.format(vlist))
        result = cls.get().create(vlist)
        return result or None
