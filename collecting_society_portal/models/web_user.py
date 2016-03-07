# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import logging

from . import Tdb

log = logging.getLogger(__name__)


class WebUser(Tdb):
    """
    Model wrapper for Tryton model object 'web.user'
    """

    __name__ = 'web.user'

    @classmethod
    @Tdb.transaction(readonly=True)
    def current_web_user(cls, request):
        """
        Fetches the currently logged in web_user

        Args:
          request (obj): request object of pyramid

        Returns:
          obj: web.user
          None: if no web_user is logged in
        """
        return cls.search_by_email(request.unauthenticated_userid)

    @classmethod
    @Tdb.transaction(readonly=True)
    def current_party(cls, request):
        """
        Fetches the party of currently logged web_user

        Args:
          request (obj): request object of pyramid

        Returns:
          obj: web.user.party
          None: if no party is logged in
        """
        return cls.current_web_user(request).party

    @classmethod
    @Tdb.transaction(readonly=True)
    def current_roles(cls, request):
        """
        Fetches the roles of currently logged in web_user

        Args:
          request (obj): request object of pyramid

        Returns:
          list: list of roles of current web_user
          None: if no web_user is logged in
        """
        current = cls.current_web_user(request)
        if current:
            return cls.roles(current)
        return None

    @classmethod
    @Tdb.transaction(readonly=True)
    def groupfinder(cls, email, request):
        """
        Fetches roles of a web_user for effective principals

        Args:
          email (str): email of web_user
          request (obj): request object of pyramid

        Returns:
          list: list of roles of current web_user
          None: if no web_user is logged in
        """
        if not email:
            return cls.current_roles(request)
        current = cls.search_by_email(email)
        if current:
            return cls.roles(current)
        return None

    @classmethod
    @Tdb.transaction(readonly=True)
    def roles(cls, web_user):
        """
        Fetches the roles of web_user

        Args:
          web_user (obj): web.user

        Returns:
          list: roles of web_user
        """
        return [role.name for role in web_user.roles]

    @classmethod
    @Tdb.transaction(readonly=True)
    def authenticate(cls, email, password):
        """
        Checks authentication of web_user with email and password

        Args:
          email (string): email of web_user
          password (string): password of web_user

        Returns:
          obj: web.user
          None: if authentication check failed
        """
        return cls.get().authenticate(email, password)

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_all(cls):
        """
        Fetches all web_user

        Returns:
          list: web.user
          None: if no match is found
        """
        return cls.get().search([])

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_by_email(cls, email):
        """
        Searches a web_user by email

        Args:
          email (string): email of web_user

        Returns:
          obj: web.user
          None: if no match is found
        """
        if email is None:
            return None
        result = cls.get().search([('email', '=', email)])
        return result[0] if result else None

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_by_id(cls, uid):
        """
        Searches a web_user by opt_in_uuid

        Args:
          uuid (string): uuid of web_user

        Returns:
          obj: web.user
          None: if no match is found
        """
        if uid is None:
            return None
        result = cls.get().search([('id', '=', uid)])
        return result[0] if result else None

    @classmethod
    @Tdb.transaction(readonly=True)
    def get_opt_in_uuid_by_id(cls, uid):
        """
        Searches a web_user by opt_in_uuid

        Args:
          uuid (string): uuid of web_user

        Returns:
          obj: web.user
          None: if no match is found
        """
        if uid is None:
            return None
        result = cls.get().search([('id', '=', uid)])
        return result[0].opt_in_uuid if result else None

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_by_uuid(cls, uuid):
        """
        Searches a web_user by opt_in_uuid

        Args:
          uuid (string): uuid of web_user

        Returns:
          obj: web.user
          None: if no match is found
        """
        if uuid is None:
            return None
        result = cls.get().search([('opt_in_uuid', '=', uuid)])
        return result[0] if result else None

    @classmethod
    @Tdb.transaction(readonly=True)
    def get_opt_in_state_by_email(cls, email):
        """
        Searches the opt_in_state for web_user by email

        Args:
          email (string): email of web_user

        Returns:
          obj: web.user
          None: if no match is found
        """
        if email is None:
            return None
        result = cls.get().search([('email', '=', email)])
        return result[0].opt_in_state if result else None

    @classmethod
    @Tdb.transaction(readonly=False)
    def update_opt_in_state_by_uuid(cls, uuid, state):
        """
        Sets the opt_in_state to 'opted_in' for the web_user

        Args:
          uuid (string): uuid of web_user

        Returns:
          obj: web.user
          None: if no match is found
        """
        if uuid is None or state is None:
            return None
        result = cls.get().search([('opt_in_uuid', '=', uuid)])
        if result:
            result[0].opt_in_state = state
            result[0].save()
            return True
        else:
            return None

    @classmethod
    @Tdb.transaction(readonly=False)
    def create(cls, vlist):
        """
        Creates web_user

        Args:
          vlist (list): list of dicts with attributes to create web_user::

            [
                {
                    'email': str (required),
                    'password': str (required)
                },
                {
                    ...
                }
            ]

        Raises:
          KeyError: if required field is missing

        Returns:
          list: created web.user
          None: if no object was created
        """
        for values in vlist:
            if 'email' not in values:
                raise KeyError('email is missing')
            if 'password' not in values:
                raise KeyError('password is missing')
        log.debug('create web_user:\n{}'.format(vlist))
        result = cls.get().create(vlist)
        return result or None
