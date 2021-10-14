# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

"""
Main module for the pyramid app.
"""

import os
import logging
from logging.config import fileConfig
import warnings

from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid_beaker import session_factory_from_settings

from .config import (
    replace_environment_vars,
    get_plugins,
    notfound
)
from .models import (
    Tdb,
    WebUser
)
from .resources import (
    WebRootFactory,
    ApiRootFactory
)

log = logging.getLogger(__name__)


def main(global_config, **settings):
    """
    Configures and creates the app.

    Handles configuration of

    - ptvsd debugging
    - app config
    - tryton database
    - session
    - policies
    - subscribers
    - route predicates
    - view predicates
    - request methods
    - translation directories
    - logging
    - root factories
    - resources
    - registry
    - views

    Contains the main logic of the plugin system by including settings,
    translation directories, logging configuration, views, ressources and
    registry information of the plugins in a well defined order.

    Args:
        global_config (dict): Parsed [DEFAULT] section of .ini file.
        **settings (dict): Parsed [app:main] section of .ini file.

    Returns:
        obj: a Pyramid WSGI application.
    """
    # supress warnings in testing environment
    warnings.filterwarnings(  # TODO: upgrade pyramid auth methods
        action="ignore", message="Authentication and authorization",
        category=DeprecationWarning)
    warnings.filterwarnings(  # TODO: upgrade pyramid auth methods
        action="ignore", message="deprecated unauthenticated_userid",
        category=DeprecationWarning)

    # get plugin configuration
    plugins = get_plugins(settings)

    # update portal settings with plugin settings and replace environment vars
    for priority in sorted(plugins, reverse=True):
        settings.update(plugins[priority]['settings'])
    settings = replace_environment_vars(settings)

    # init app config
    config = Configurator(settings=settings)

    # configure tryton database
    Tdb._db = settings['tryton.database']
    Tdb._company = settings['tryton.company']
    Tdb._user = settings['tryton.user']
    Tdb._configfile = settings['tryton.configfile']
    Tdb.init()

    # configure session
    config.set_session_factory(factory=session_factory_from_settings(settings))

    # configure policies
    config.set_authorization_policy(policy=ACLAuthorizationPolicy())
    config.set_authentication_policy(
        policy=AuthTktAuthenticationPolicy(
            secret=settings['authentication.secret'],
            hashalg='sha512',
            callback=WebUser.groupfinder))
    config.set_default_permission('administrator')

    # configure subscribers
    config.add_subscriber(
        subscriber='.config.add_templates',
        iface='pyramid.events.BeforeRender')
    config.add_subscriber(
        subscriber='.config.add_helpers',
        iface='pyramid.events.BeforeRender')
    config.add_subscriber(
        subscriber='.config.add_locale',
        iface='pyramid.events.NewRequest')
    config.add_subscriber(
        subscriber='.config.open_db_connection',
        iface='pyramid.events.BeforeTraversal')
    config.add_subscriber(
        subscriber='.config.context_found',
        iface='pyramid.events.ContextFound')
    config.add_subscriber(
        subscriber='.config.close_db_connection',
        iface='pyramid.events.NewRequest')
    if settings['env'] in ['development', 'staging']:
        config.add_subscriber(
            subscriber='.config.debug_request',
            iface='pyramid.events.NewRequest')
        config.add_subscriber(
            subscriber='.config.debug_context',
            iface='pyramid.events.ContextFound')
        config.add_subscriber(
            subscriber='.config.debug_response',
            iface='pyramid.events.NewResponse')

    # configure predicates
    config.add_route_predicate(
        name='environment', factory='.config.Environment')
    config.add_view_predicate(
        name='environment', factory='.config.Environment')

    # configure request methods
    config.add_request_method(
        callable='.config.web_user', name='web_user', reify=True)
    config.add_request_method(
        callable='.config.party', name='party', reify=True)
    config.add_request_method(
        callable='.config.user', name='user', reify=True)
    config.add_request_method(
        callable='.config.roles', name='roles', reify=True)

    # configure translation directories for portal and plugins
    config.add_translation_dirs(
        'colander:locale/',
        'deform:locale/',
        'portal_web:locale/')
    for priority in sorted(plugins):
        translation_dir = os.path.join(
            plugins[priority]['path'], plugins[priority]['name'], 'locale')
        print(translation_dir)
        if os.path.isdir(translation_dir):
            config.add_translation_dirs(translation_dir)

    # configure logging for portal and plugins
    for priority in sorted(plugins):
        fileConfig(
            plugins[priority]['path'] + '/' + settings['env'] + '.ini',
            disable_existing_loggers=False)

    # commit config with basic settings
    config.commit()

    # not found view (404 Error)
    config.add_notfound_view(notfound)

    # configure mailer
    if int(settings['mail.to_real_world']):
        config.include('pyramid_mailer')
    else:
        config.include('pyramid_mailer.testing')

    # enable ptvsd debugging (open port 51000 for portal and 51001 for api!)
    if int(settings['debugger.ptvsd']):
        debugging_port = 0
        if settings['service'] == 'webgui':
            debugging_port = 51000
        if settings['service'] == 'webapi':
            debugging_port = 51001
        if debugging_port > 0:
            log.debug(settings['service'] + " debugger listening to port " +
                      str(debugging_port))
            try:
                import ptvsd  # unconditional import breaks test coverage
                ptvsd.enable_attach(address=("0.0.0.0", debugging_port),
                                    redirect_output=True)
                # uncomment these three lines, and set the debugging_port
                # accordingly, if you need to debug initialization code
                # like colander schema nodes, for example:
                # if debugging_port == 51001:
                #     ptvsd.wait_for_attach()
                #     ptvsd.break_into_debugger()
            except Exception as ex:
                if hasattr(ex, 'message'):
                    log.debug(ex.message)
                else:
                    log.debug('ptvsd debugging not possible: ' + ex.message)

    # configure webfrontend for portal and plugins
    if settings['service'] == 'webgui':
        # web root factory
        config.set_root_factory(factory=WebRootFactory)
        # web resources
        config.include('.includes.web_resources')
        for priority in sorted(plugins):
            config.include(plugins[priority]['name']+'.includes.web_resources')
        # web registry
        config.include('.includes.web_registry')
        for priority in sorted(plugins):
            config.include(plugins[priority]['name']+'.includes.web_registry')
        # web views
        for priority in sorted(plugins, reverse=True):
            config.include(plugins[priority]['name'] + '.includes.web_views')
        config.include('.includes.web_views')
        # api views
        if settings['api.in_web'] == 'true':
            config.include('cornice')
            for priority in sorted(plugins, reverse=True):
                config.include(
                    plugins[priority]['name'] + '.includes.api_views',
                    route_prefix=settings['api.in_web_path'])
            config.include(
                '.includes.api_views',
                route_prefix=settings['api.in_web_path'])

    # configure api for portal and plugins
    if settings['service'] == 'webapi':
        config.include('cornice')
        config.include('cornice_swagger')
        # api root factory
        config.set_root_factory(factory=ApiRootFactory)
        # api views
        for priority in sorted(plugins, reverse=True):
            config.include(plugins[priority]['name'] + '.includes.api_views')
        config.include('.includes.api_views')

    return config.make_wsgi_app()
