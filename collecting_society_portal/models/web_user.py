# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import logging

from . import Tdb

log = logging.getLogger(__name__)


class WebUser(Tdb):
    """
    Model wrapper for Tryton model object 'web.user'.
    """

    __name__ = 'web.user'

    @classmethod
    @Tdb.transaction(readonly=True)
    def current_web_user(cls, request):
        """
        Gets the currently logged in web user.

        Args:
            request (pyramid.request.Request): Current request.

        Returns:
            obj (web.user): Web user.
            None: If no web user is logged in.
        """
        return cls.search_by_email(request.unauthenticated_userid)

    @classmethod
    @Tdb.transaction(readonly=True)
    def current_party(cls, request):
        """
        Gets the party of the currently logged in web user.

        Args:
            request (pyramid.request.Request): Current request.

        Returns:
            obj (web.user.party): Party of the web user.
            None: If no web user is logged in
        """
        current = cls.current_web_user(request)
        if current:
            return cls.current_web_user(request).party
        return None

    @classmethod
    @Tdb.transaction(readonly=True)
    def current_roles(cls, request):
        """
        Gets the roles of the currently logged in web user.

        Args:
            request (pyramid.request.Request): Current request.

        Returns:
            list: List of roles of the current web user.
            None: If no web user is logged in.
        """
        current = cls.current_web_user(request)
        if current:
            return cls.roles(current)
        return None

    @classmethod
    @Tdb.transaction(readonly=True)
    def groupfinder(cls, email, request):
        """
        Gets the roles of a web user for effective principals.

        Args:
            email (str): Email of the web user.
            request (pyramid.request.Request): Current request.

        Returns:
            list: List of roles of the current web user.
            None: If no web user is logged in.
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
        Gets the roles of a web user.

        Args:
            web_user (obj[web.user]): Web user.

        Returns:
            list: List of roles of the web user.
        """
        return [role.name for role in web_user.roles]

    @classmethod
    @Tdb.transaction(readonly=True)
    def authenticate(cls, email, password):
        """
        Checks authentication of a web user with email and password.

        Args:
            email (str): Email of the web user.
            password (str): Password of the web user.

        Returns:
            obj (web.user): Web user.
            None: If authentication check failed.
        """
        return cls.get().authenticate(email, password)

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_all(cls):
        """
        Gets all web users.

        Returns:
            list (obj[web.user]): List of web users.
            None: if no match is found.
        """
        return cls.get().search([])

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_by_email(cls, email):
        """
        Searches a web user by email.

        Args:
            email (str): Email of the web_user

        Returns:
            obj (web.user): Web user.
            None: If no match is found.
        """
        if email is None:
            return None
        result = cls.get().search([('email', '=', email)])
        return result[0] if result else None

    @classmethod
    @Tdb.transaction(readonly=False)
    def create(cls, vlist):
        """
        Creates web users.

        Args:
            vlist (list): List of dictionaries with attributes of a web user.
                [
                    {
                        'email': str (required),
                        'password': str (required)
                    },
                    {
                        ...
                    }
                ]

        Returns:
            list (obj[web.user]): List of created web users.
            None: If no object was created.

        Raises:
            KeyError: If required field is missing.
        """
        for values in vlist:
            if 'email' not in values:
                raise KeyError('email is missing')
            if 'password' not in values:
                raise KeyError('password is missing')
        log.debug('create web_user:\n{}'.format(vlist))
        result = cls.get().create(vlist)
        return result or None
