# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

import datetime

import logging

from . import Tdb, MixinSearchByCode

log = logging.getLogger(__name__)


class Checksum(Tdb, MixinSearchByCode):
    """
    Model wrapper for Tryton model object 'checksum'.
    """

    __name__ = 'checksum'

    @classmethod
    def search_collision(cls, code, algorithm=None, begin=None, end=None):
        """
        Searches for a checksum collision.

        Args:
            begin (int): First byte for checksum.
            end (int): Last byte for checksum.
            algorithm (str): Algorithm for checksum.
            code (str): Code of checksum.

        Returns:
            list (obj[Checksum]): List of collided checksums.
            list ([]): If no match is found.
        """
        if code is None:
            return []
        query = [('code', '=', code)]
        if begin:
            query.append(('begin', '=', begin))
        if end:
            query.append(('end', '=', end))
        if algorithm:
            query.append(('algorithm', '=', algorithm))
        return cls.get().search(query)

    @classmethod
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
        log.debug('create {} checksums'.format(len(vlist)))
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
