# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import datetime

import logging

from . import Tdb

log = logging.getLogger(__name__)


class Checksum(Tdb):
    """
    Model wrapper for Tryton model object 'checksum'.
    """

    __name__ = 'checksum'

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_by_code(cls, code):
        """
        Searches a checksum by code.

        Args:
            code (str): Code of checksum.

        Returns:
            obj: Checksum.
            None: If no match is found.
        """
        if code is None:
            return None
        result = cls.get().search([('code', '=', code)])
        return result[0] if result else None

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_collision(cls, code, begin, end):
        """
        Searches for a checksum collision.

        Args:
            code (str): Code of checksum.
            begin (int): First byte for checksum.
            end (int): Last byte for checksum.

        Returns:
            obj: Checksum.
            None: If no match is found.
        """
        if code is None:
            return None
        if begin is None:
            return None
        if end is None:
            return None
        result = cls.get().search([
            ('code', '=', code),
            ('begin', '=', begin),
            ('end', '=', end),
            ('origin.duplicate_of', '=', None),
        ])
        return result[0] if result else None

    @classmethod
    @Tdb.transaction(readonly=False)
    def create(cls, vlist):
        """
        Creates a checksum.

        Args:
            vlist (list): List of dictionaries with attributes of a checksum.
                [
                    {
                        'origin': obj content||harddisk (required),
                        'code': str (required)
                        'timestamp': obj (required),
                        'algorithm': str (required),
                        'begin': int,
                        'end': int
                    },
                    {
                        ...
                    }
                ]

        Returns:
            list (obj[checksum]): List of created bank account
                numbers.
            None: If no object was created.

        Raises:
            KeyError: If required field is missing.
            NotImplementedError: If type is not implemented.
        """
        log.debug('create checksum:\n{}'.format(vlist))
        for values in vlist:
            if 'origin' not in values:
                raise KeyError('origin is missing')
            if 'code' not in values:
                raise KeyError('code is missing')
            if 'algorithm' not in values:
                raise KeyError('algorithm is missing')
            if 'timestamp' not in values:
                values['timestamp'] = datetime.datetime.now()
        result = cls.get().create(vlist)
        return result or None
