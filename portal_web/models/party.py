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
    def is_foreign_editable(cls, web_user, party):
        """
        Checks if the party is a foreign object and still editable by the
        current webuser.

        Checks, if the member
            1) is a foreign object
            2) is still not claimed yet
            3) is editable by the current web user
            4) TODO: was not part of a distribution yet

        Args:
          web_user (obj): Current web user.
          party (obj): Party to check.

        Returns:
          true: if member is editable.
          false: otherwise.
        """
        # TODO: check rightsholder domain
        # 1) is a foreign object
        if party.entity_origin != 'indirect':
            return False
        # 2) is still not claimed yet
        if party.claim_state != 'unclaimed':
            return False
        # 3) is editable by the current web user
        if party.entity_creator != web_user.party:
            return False
        # 4) TODO: was not part of a distribution yet
        return True

    @staticmethod
    def get_rightsholder_domain(web_user=None):
        domain = ['OR']
        if web_user:
            domain += [
                ('id', '=', web_user.party.id),
                [
                    ('entity_origin', '=', 'indirect'),
                    ('entity_creator', '=', web_user.party),
                ],
            ]
        domain += [
            ('collecting_societies.id', '>', 0),
            ('labels.id', '>', 0),
            ('publishers.id', '>', 0),
            ('artists.id', '>', 0),
            ('creation_rights.id', '>', 0),
            ('release_rights.id', '>', 0),
        ]
        return domain

    @classmethod
    def search_rightsholder(
            cls, domain=[], offset=None, limit=None, order=None, escape=False,
            active=True, web_user=None):
        """
        Searches rightsholder parties by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          obj: list of parties
        """
        domain = [Party.get_rightsholder_domain(web_user), domain]
        # prepare query
        if escape:
            domain = cls.escape_domain(domain)
        if active:
            domain.append(('active', 'in', (True, active)))
        # search
        result = cls.get().search(domain, offset, limit, order)
        return result

    @classmethod
    def search_count_rightsholder(cls, domain, escape=False, active=True,
                                  web_user=None):
        """
        Counts rightholder parties by domain

        Args:
          domain (list): domain passed to tryton

        Returns:
          int: number of parties
        """
        domain = [Party.get_rightsholder_domain(web_user)] + domain
        # prepare query
        if escape:
            domain = cls.escape(domain)
        if active:
            domain.append(('active', 'in', (True, active)))
        # search
        result = cls.get().search_count(domain)
        return result

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
    def search_by_oid(cls, oid):
        """
        Searches a party by oid.

        Args:
            oid (string): oid of the party.

        Returns:
            obj (party.party): Party.
            None: If no match is found.
        """
        if oid is None:
            return None
        result = cls.get().search([('oid', '=', oid)])
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
        log.debug(vlist)
        result = cls.get().create(vlist)
        return result or None

    @classmethod
    def create_foreign(cls, party, name, email, group=False):
        """
        Creates foreign Party

        Args:
            party: the Party that wants to create the foreign objects
            name: the artist name of the foreign artist object
            email: the artist email of the foreign artist object

        Returns:
            Artist object: the artist that has been created
            None: if no object was created
        """
        assert name
        assert email
        foreign_party = Party.create([{
            'name': name,
            'contact_mechanisms': [(
                'create', [{
                    'type': 'email',
                    'value': email
                }]
            )],
            'entity_creator': party,
            'entity_origin': 'indirect',
            'claim_state': 'unclaimed',
        }])
        if not foreign_party:
            return None
        return foreign_party[0]
