# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

from functools import wraps

from trytond.transaction import Transaction
from trytond.cache import Cache
from trytond.config import config
from trytond import backend
from trytond.pool import Pool


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
        config.update_etc(str(cls._configfile))
        cls._retry = config.getint('database', 'retry')
        with Transaction().start(str(cls._db), int(cls._user), readonly=True):
            Pool().init()

    def transaction(readonly=None, user=None, context=None, withhold=False):
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

        class NoTransaction():
            """Dummy context manager to avoid duplicate code."""

            def __enter__(self):
                return None

            def __exit__(self, type, value, traceback):
                pass

        def default_context():
            pool = Pool(str(Tdb._db))
            user = pool.get('res.user')
            return user.get_preferences(context_only=True)

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                _db = Tdb._db
                _readonly = True
                if readonly is not None:
                    _readonly = readonly
                elif 'request' in kwargs:
                    _readonly = not (kwargs['request'].method
                                     in ('PUT', 'POST', 'DELETE', 'PATCH'))
                _user = user or 0
                _context = {}

                _retry = Tdb._retry or 0
                _is_open = (Transaction().cursor)

                if not _is_open:
                    with Transaction().start(_db, 0):
                        Cache.clean(_db)
                        _context.update(default_context())
                else:
                    # Transaction().new_cursor(readonly=_readonly)
                    pass
                _context.update(context or {})
                # _context.update({'company': Tdb._company})

                for count in range(_retry, -1, -1):
                    with NoTransaction() if _is_open else Transaction().start(
                            _db, _user, readonly=_readonly, context=_context):
                        cursor = Transaction().cursor
                        if withhold:
                            cursor.cursor.withhold = True
                        try:
                            result = func(*args, **kwargs)
                            if not _readonly:
                                cursor.commit()
                        except DatabaseOperationalError:
                            cursor.rollback()
                            if count and not _readonly:
                                continue
                            raise
                        except Exception:
                            cursor.rollback()
                            raise
                        Cache.resets(_db)
                        return result
            return wrapper
        return decorator

    @classmethod
    @transaction(readonly=True)
    def pool(cls):
        """
        Gets the Tryton pool object.

        Returns:
            obj: Pool.
        """
        pool = Pool(str(cls._db))
        return pool

    @classmethod
    @transaction(readonly=True)
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
    @transaction(readonly=True)
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
