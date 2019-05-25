# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import logging

from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import (
    view_config,
    view_defaults
)
from psycopg2 import (
    DatabaseError,
    OperationalError
)

from ..services import benchmarks
from ..models import Tdb
from ..views import ViewBase

log = logging.getLogger(__name__)


@view_defaults(
    context='..resources.DebugResource',
    permission=NO_PERMISSION_REQUIRED,
    environment="development")
class DebugViews(ViewBase):

    @view_config(
        name='tryton',
        renderer='../templates/debug/tryton.pt',
        decorator=Tdb.transaction())
    def check_tryton(self, request):
        '''
        This view should display some useful information
        about Tryton and the database backend.

        Is the PostGresDB running?
        Are there any databases present?
        Shall we recreate them now?

        createdb -h 127.0.0.1 -p 5432 -U postgres -O postgres -w -E UTF-8 c3s
        env/bin/trytond -d c3s -c etc/trytond.conf --all
        env/bin/python -m doctest -v etc/scenario_master_data.txt

        returns a dictionary of values to render with the template
        '''
        # request.session.pop_flash('tryton_database_checking')
        the_result = {
            'is_postgres_up': True,  # expect the best ;-)
            'db_exists_at_all': True,
            'databases': [],
            'database_name': '',
            'object_name_list': []
        }
        # check connection status
        try:
            Tdb.pool()
        except AttributeError as ae:  # pragma: no cover
            log.debug('hit an AttributeError! \n%s' % ae)
        except DatabaseError as dbe:  # pragma: no cover
            log.debug('hit a database error: %s') % dbe
            the_result['db_exists_at_all'] = 'the database does not exist!'
            request.session.flash(
                dbe,
                'tryton_database_checking'
            )
        except OperationalError as oe:  # pragma: no cover
            if 'does not exist' in oe.message:
                log.debug('---- Operational Error: %s') % oe
        the_result['is_postgres_up'] = True
        the_result['db_exists_at_all'] = False

        # check for existing databases
        try:
            the_result['databases'] = Tdb.pool().database_list()
            log.debug('databases: %s' % the_result['databases'])
        except OperationalError as oe:  # pragma: no cover
            log.debug('hit OperationalError oe: {}'.format(oe))

        # check for existing databases
        try:
            the_result['database_name'] = Tdb.pool().database_name
            log.debug('database_name: %s' % the_result['database_name'])
        except OperationalError as oe:  # pragma: no cover
            pass

        # check for object classes in tryton pool
        try:
            the_result['object_name_list'] = sorted(
                Tdb.pool().object_name_list()
            )

            log.debug('object_classes: %s' % the_result['object_name_list'])
        except OperationalError as oe:  # pragma: no cover
            pass
        except KeyError as ke:  # pragma: no cover
            log.debug('hit the KeyError: %s' % ke)

        return the_result

    @view_config(
        name='benchmark',
        renderer='../templates/debug/benchmark.pt')
    def benchmark(self):
        delete = ('delete' in self.request.POST or self.request.GET)
        log.debug(self.request.POST)
        return benchmarks(delete)
