# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

import logging
from functools import wraps

from psycopg2._psycopg import InterfaceError

from pyramid import threadlocal

from trytond.transaction import Transaction
from trytond.cache import Cache
from trytond.config import config
from trytond import backend
from trytond.pool import Pool

log = logging.getLogger(__name__)


class Tdb(object):
    """
    Base Class for model wrappers and communication handling using trytond.

    Includes functions to

    - initialize the tryton database
    - wrap database communication with transaction handling

    Includes helper functions for getting the pool, context and models.

    Classattributes:
        _db (str): Name of database.
        _configfile (str): Tryton config file.
        _retry (int): Number of retries in transactions.
        _user (int): Default id of tryton backend user for transactions.
        _company (int): Default company id.
        __name__ (str): Name of the tryton model to be initialized.
    """

    wraps = 0  # debug information

    # --- DB ------------------------------------------------------------------

    _db = None
    _configfile = None
    _retry = None
    _user = None
    _company = None

    @classmethod
    def init(cls):
        """
        Initializes a Tryton database.

        Configuration is done by assigning the desired values to the following
        class attributes prior to the call:

        - _db
        - _configfile
        - _company
        - _user

        Updates the tryton config and reads out the configured number of
        retries before initialization.

        Note:
            This function is expected to be called only once.

        Examples:
            >>> Tdb._db = 'db'
            >>> Tdb._configfile = '/path/to/configfile'
            >>> Tdb._company = 1
            >>> Tdb._user = 'user'
            >>> Tdb.init()
        """
        if cls.is_open():
            return

        config.update_etc(str(cls._configfile))
        cls._retry = config.getint('database', 'retry')
        with Transaction().start(str(cls._db), int(cls._user), readonly=True):
            Pool().init()

    @staticmethod
    def is_open():
        if Transaction().cursor and not Transaction().cursor._conn.closed:
            return True
        return False

    def transaction(readonly=None, user=None, context=None):
        """
        Decorater function to wrap database communication with transactions.

        The wrapping function handles:

        - start and stop of transactions
        - caching in case of multithreading environments
        - commit and rollback of cursors on error
        - retries in case of an operational error of Tryton
        - chaining of multiple decorated functions within one transaction

        2DO: Chaining multiple calls to the database could result in different
        cursors. This works in principle (commented out) but still has a
        problem with the combination of different rw/ro calls.

        Args:
            readonly (bool): Type of transaction.
                If None and kwargs contains a request object, then the
                transaction will be readonly except for PUT, POST, DELETE
                and PATCH request methods.
                If None and kwargs contains no request object, then
                the transaction will be readonly.
            user (int): Tryton backend user id for transaction.
                If None, then the default user will be used for transaction
            context (dict): Context for transaction.
                If None, then the context of transaction will be empty.

        Raises:
            DatabaseOperationalError: if Tryton or the database has a problem.

        Note:
            This work is based on the `flask_tryton`_ package by Cedric Krier
            <ced@b2ck.com> licensed under GPLv3 (see `flask_tryton.py`)

        .. _flask_tryton:
            https://pypi.python.org/pypi/flask_tryton
        """
        DatabaseOperationalError = backend.get('DatabaseOperationalError')
        _tdbglog = "/ado/tmp/transaction.log"

        def _tdbg(func, mode, string=None, levelchange=0):
            settings = threadlocal.get_current_registry().settings
            if not settings or 'debug.tdb.transactions' not in settings:
                return
            if settings['debug.tdb.transactions'] == 'true':
                import os
                import inspect
                stack = inspect.stack()
                _, filename, line_number, function, lines, _ = stack[2]
                functions = []
                for i, framerecord in enumerate(stack):
                    f = framerecord[3]
                    if f in ['<lambda>', '_call_view']:
                        break
                    if f in ['_tdbg', 'wrapper']:
                        continue
                    functions.append(f)
                functions.reverse()
                with open(_tdbglog, "a") as f:
                    lvl = Tdb.wraps if mode == "WRAP" else Tdb.wraps - 1
                    f.write("\t"*Tdb.wraps + "%s %s" % (mode, func.__name__))
                    f.write(" %s" % lvl)
                    if mode == "WRAP":
                        f.write(" | %s:%s():%s %s\n" % (
                            os.path.basename(filename), function, line_number,
                            lines[0].strip()))
                        f.write(
                            "\t"*(Tdb.wraps+1)+"- connection: %s, %s\n" % (
                                Tdb.is_open() and "open" or "closed",
                                readonly and "read" or "write"))
                        f.write("\t"*(Tdb.wraps+1)+"- calls:  %s" % (
                            " -> ".join(functions)))
                    if string:
                        f.write(" | " + string)
                    f.write("\n")
                    Tdb.wraps += levelchange
                    if not Tdb.wraps:
                        f.write("\n")
                os.chmod(_tdbglog, 775)

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                _db = Tdb._db
                _user = user or 0
                _retry = Tdb._retry or 0
                _readonly = readonly
                if 'request' in kwargs:
                    _readonly = not (
                        kwargs['request'].method
                        in ('PUT', 'POST', 'DELETE', 'PATCH'))
                _tdbg(func, "WRAP", None, 1)

                for count in range(_retry, 0, -1):
                    if not Tdb.is_open():
                        _tdbg(func, "CONNECT")
                        with Transaction().start(_db, 0):
                            Cache.clean(_db)
                            pool = Pool(Tdb._db)
                            User = pool.get('res.user')
                            _context = User.get_preferences(context_only=True)
                            _context.update(context or {})
                        Transaction().start(
                            _db, _user, readonly=_readonly, context=_context,
                            close=False)

                    cursor = Transaction().cursor
                    try:
                        _tdbg(func, "CALL", "Try %s, Cursor %s" %
                              (_retry + 1 - count, id(cursor)))
                        result = func(*args, **kwargs)
                        if not _readonly:
                            _tdbg(func, "COMMIT", "Try %s, Cursor %s" %
                                  (_retry + 1 - count, id(cursor)))
                            cursor.commit()
                    except DatabaseOperationalError:
                        if cursor:
                            cursor.rollback()
                        if not count or _readonly:
                            raise
                        continue
                    except InterfaceError:
                        if cursor:
                            cursor.rollback()
                        if not count:
                            raise
                        continue
                    except Exception:
                        if cursor:
                            cursor.rollback()
                        raise

                    _tdbg(func, "RETURN", None, -1)
                    return result
            return wrapper
        return decorator

    @classmethod
    def pool(cls):
        """
        Gets the Tryton pool object.

        Returns:
            obj: Pool.
        """
        pool = Pool(str(cls._db))
        return pool

    @classmethod
    def context(cls):
        """
        Gets the Transaction context.

        Returns:
            dict: Context.
        """
        context = Transaction().context
        return context

    # --- Model ---------------------------------------------------------------

    __name__ = None

    @classmethod
    def get(cls, model=None):
        """
        Gets a Tryton model object.

        If no Tryton model descriptor is passed, the class variable __name__ is
        assumed to be set to it's default Tryton model descriptor, which then
        will be used to get the Tryton model.

        Args:
            model (str): Tryton model descriptor or None.

        Returns:
            obj: Tryton model.
        """
        pool = cls.pool()
        if model:
            return pool.get(str(model))
        if not cls.__dict__['__name__']:
            raise KeyError("__name__ is missing")
        return pool.get(str(cls.__dict__['__name__']))

    transaction = staticmethod(transaction)

    # --- Methods -------------------------------------------------------------

    @classmethod
    def escape(cls, string, wrap=False):
        string = string.replace('_', '\\_')
        string = string.replace('%', '\\_')
        if wrap:
            string = "%" + string + "%"
        return string

    @classmethod
    def escape_domain(cls, domain, wrap=True):
        for index, statement in enumerate(domain):
            if isinstance(statement, (list,)):
                cls.escape_operands(statement)
            if isinstance(statement, basestring):  # noqa: F821
                continue
            if statement[1] in ['like', 'ilike', 'not like', 'not ilike']:
                statement_list = list(statement)
                statement_list[2].replace('_', '\\_')
                statement_list[2].replace('%', '\\_')
                if wrap:
                    statement_list[2] = "%" + statement_list[2] + "%"
                domain[index] = tuple(statement_list)
        return domain

    @classmethod
    def create(cls, vlist):
        """
        Generic creation method to use in model wrappers.

        Args:
          vlist (list): list of dicts with attributes to create records.
                        For example::

            [
                {
                    'code': ...,
                    'uuid': ...,
                    'name': ...
                },
                {
                    ...
                }
            ]

        Raises:
          KeyError: if required field is missing

        Returns:
          list: created devices
          None: if no object was created
        """
        log.debug('create database object:\n{}'.format(vlist))
        result = cls.get().create(vlist)
        return result or None


class MixinSearchById(object):
    """
    Modelwrapper mixin for models that can be searched by id
    """
    @classmethod
    def search_by_id(cls, id):
        """
        Searches a model by id

        Args:
          id (int): model.id

        .. note::
          This is a search for the internal database id.

        Returns:
          obj: model
          None: if no match is found
        """
        result = cls.get().search([('id', '=', int(id))])
        if not result:
            return None
        return result[0]

class MixinSearchByCode(object):
    """
    Modelwrapper mixin for models that can be searched by its code
    """
    @classmethod
    def search_by_code(cls, code):
        """
        Searches an object by its code.

        Args:
            code (str): Code of the object.

        Returns:
            obj: Checksum.
            None: If no match is found.
        """
        if code is None:
            return None
        result = cls.get().search([('code', '=', code)])
        return result[0] if result else None

class MixinSearchByName(object):
    """
    Modelwrapper mixin for models that can be searched by its name field
    """
    @classmethod
    def search_by_name(cls, name):
        """
        Searches an object by name

        Args:
          name (string): object.name

        Returns:
          obj: db object
          None: if no match is found
        """
        result = cls.get().search([('name', '=', name)])
        return result[0] or None

class MixinSearchByUuid(object):
    """
    Modelwrapper mixin for models that can be searched by its UUID field
    """
    @classmethod
    def search_by_uuid(cls, uuid):
        """
        Searches an object by uuid

        Args:
          uuid (string): object.uuid

        Returns:
          obj: db object
          None: if no match is found
        """
        result = cls.get().search([('uuid', '=', uuid)])
        return result[0] or None


class MixinWebuser(object):
    """
    Modelwrapper mixin for models that need to filter by webusers acl
    restrictions, for example if the webuser is allowed to view or edit items.

    """
    @classmethod
    def current_viewable(cls, request):
        """
        Searches objects, which the current web_user is allowed to view.

        Args:
          request (pyramid.request.Request): Current request.

        Returns:
          list: viewable objects of web_user
          None: if no match is found
        """
        return cls.search_viewable_by_web_user(request.web_user.id)

    @classmethod
    def current_editable(cls, request):
        """
        Searches objects, which the current web_user is allowed to edit.

        Args:
          request (pyramid.request.Request): Current request.

        Returns:
          list: editable objects of web_user
          None: if no match is found
        """
        return cls.search_editable_by_web_user(request.web_user.id)

    @classmethod
    def search_viewable_by_web_user(cls, web_user_id, active=True):
        """
        Searches objects, which the web_user is allowed to view.
        The view permission is expected to have the form 'view_<modelname>'.

        Args:
          web_user_id (int): web.user.id

        Returns:
          list: viewable objects of web_user, empty if none were found
        """
        return cls.get().search([
            ('acl.web_user', '=', web_user_id),
            ('acl.roles.permissions.code', '=', 'view_' +
             cls.__dict__['__name__'])
        ])

    @classmethod
    def search_editable_by_web_user(cls, web_user_id, active=True):
        """
        Searches objects, which the web_user is allowed to edit.
        The view permission is expected to have the form 'edit_<modelname>'.

        Args:
          web_user_id (int): web.user.id

        Returns:
          list: viewable objects of web_user, empty if none were found
        """
        return cls.get().search([
            ('acl.web_user', '=', web_user_id),
            ('acl.roles.permissions.code', '=', 'edit_' +
             cls.__dict__['__name__'])
        ])
