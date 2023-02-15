# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

import logging

from . import Tdb, MixinSearchByName

log = logging.getLogger(__name__)


class Party(Tdb, MixinSearchByName):
    """
    Model wrapper for Tryton model object 'party.party'.
    """

    __name__ = 'party.party'

    @classmethod
    def search_all(cls):
        """
        Gets all parties.

        Returns:
            list (obj[party.party]): List of parties.
            None: if no match is found.
        """
        return cls.get().search([])

    @classmethod
    def search_by_id(cls, uid):
        """
        Searches a party by id.

        Args:
            uid (string): Id of the party.

        Returns:
            obj (party.party): Party.
            None: If no match is found.
        """
        if uid is None:
            return None
        result = cls.get().search([('id', '=', uid)])
        return result[0] if result else None

    @classmethod
    def search_by_email(cls, email):
        """
        Searches a party by email.

        Args:
            email (str): Email of the party.

        Returns:
            obj (party.party): Party.
            None: If no match is found.
        """
        if email is None:
            return None
        result = cls.get().search([('email', '=', email)])
        return result[0] if result else None

    @classmethod
    def create(cls, vlist):
        """
        Creates parties.

        Args:
            vlist (list): List of dictionaries with attributes of a party.
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
            list (obj[party.party]): List of created parties.
            None: If no object was created.

        Raises:
            KeyError: If required field is missing.
        """
        for values in vlist:
            if 'name' not in values:
                raise KeyError('name is missing')
        log.debug('create party:\n{}'.format(vlist))
        result = cls.get().create(vlist)
        return result or None
