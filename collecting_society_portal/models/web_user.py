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
    def current_web_user(cls, request):
        """
        Gets the currently logged in web user.

        Args:
            request (pyramid.request.Request): Current request.

        Returns:
            obj (web.user): Web user.
            None: If no web user is logged in.
        """
        userid = request.authenticated_userid
        if not userid:
            return None
        return cls.search_by_email(userid)

    @classmethod
    def current_party(cls, request):
        """
        Gets the party of the currently logged in web user.

        Args:
            request (pyramid.request.Request): Current request.

        Returns:
            obj (web.user.party): Party of the web user.
            None: If no web user is logged in
        """
        if not request.web_user:
            return None
        return request.web_user.party

    @classmethod
    def current_user(cls, request):
        """
        Gets the party of the currently logged in web user.

        Args:
            request (pyramid.request.Request): Current request.

        Returns:
            obj (web.user.party): Party of the web user.
            None: If no web user is logged in
        """
        if not request.web_user:
            return None
        return request.web_user.user

    @classmethod
    def current_roles(cls, request):
        """
        Gets the roles of the currently logged in web user.

        Args:
            request (pyramid.request.Request): Current request.

        Returns:
            list: List of roles of the current web user.
            None: If no web user is logged in.
        """
        if not request.web_user:
            return None
        return [role.code for role in request.web_user.roles]

    @classmethod
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
        web_user = cls.search_by_email(email)
        if web_user:
            return cls.roles(web_user)
        return None

    @classmethod
    def roles(cls, web_user):
        """
        Gets the roles of a web user.

        Args:
            web_user (obj[web.user]): Web user.

        Returns:
            list: List of roles of the web user.
        """
        return [role.code for role in web_user.roles]

    @classmethod
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

        # code copied from ado/src/web_user/user.py and
        # modified to support case-insensitive email addresses
        users = cls.get().search([('email', 'ilike', cls.escape(email))])
        if not users:
            return
        user, = users
        if cls.get().check_password(password, user.password_hash):
            return user

    @classmethod
    def search_all(cls):
        """
        Gets all web users.

        Returns:
            list (obj[web.user]): List of web users.
            None: if no match is found.
        """
        return cls.get().search([])

    @classmethod
    def search_by_id(cls, uid):
        """
        Searches a web user by id.

        Args:
            uid (string): Id of the web user.

        Returns:
            obj (web.user): Web user.
            None: If no match is found.
        """
        if uid is None:
            return None
        result = cls.get().search([('id', '=', uid)])
        return result[0] if result else None

    @classmethod
    def search_by_email(cls, email):
        """
        Searches a web user by email.

        Args:
            email (str): Email of the web user.

        Returns:
            obj (web.user): Web user.
            None: If no match is found.
        """
        if email is None:
            return None
        result = cls.get().search([('email', 'ilike', cls.escape(email))])
        return result[0] if result else None

    @classmethod
    def search_by_opt_in_uuid(cls, opt_in_uuid):
        """
        Searches a web user by opt in uuid.

        Args:
            opt_in_uuid (string): Opt in uuid of the web user.

        Returns:
            obj (web.user): Web user.
            None: If no match is found.
        """
        if opt_in_uuid is None:
            return None
        result = cls.get().search([('opt_in_uuid', '=', opt_in_uuid)])
        return result[0] if result else None

    @classmethod
    def get_opt_in_uuid_by_id(cls, uid):
        """
        Searches an opt in uuid by web user id.

        Args:
            uid (string): Id of the web user.

        Returns:
            str: Opt in uuid.
            None: If no match is found.
        """
        if uid is None:
            return None
        web_user = cls.search_by_id(uid)
        if web_user:
            return web_user.opt_in_uuid
        return None

    @classmethod
    def get_opt_in_state_by_email(cls, email):
        """
        Searches the opt in state for the web user by email.

        Args:
            email (string): Email of the web user.

        Returns:
            str: Opt in state.
            None: If no match is found.
        """
        if email is None:
            return None
        web_user = cls.search_by_email(email)
        if web_user:
            return web_user.opt_in_state
        return None

    @classmethod
    def update_opt_in_state(cls, opt_in_uuid, state):
        """
        Sets the opt in state for the web user.

        Args:
            opt_in_uuid (string): Opt in uuid of the web user.
            state (string): New opt in state.

        Returns:
            True: If update was successful.
            False: Otherwise.
        """
        if opt_in_uuid is None:
            return False
        web_user = cls.search_by_opt_in_uuid(opt_in_uuid)
        if web_user:
            web_user.opt_in_state = state
            web_user.save()
            return True
        return False

    @classmethod
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
        result = cls.get().create(vlist)
        for wu in vlist:
            if 'password' in wu:
                wu['password'] = '********'
        log.debug('create web_user:\n{}'.format(vlist))
        return result or None
