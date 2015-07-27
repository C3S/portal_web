# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

from logging.config import fileConfig

from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid_beaker import session_factory_from_settings

from .config import (
    replace_environment_vars,
    get_plugins
)
from .models import (
    Tdb,
    WebUser
)
from .resources import (
    WebRootFactory,
    ApiRootFactory
)


def main(global_config, **settings):
    """
    Configures and creates the app

    Args:
      global_config: Global configuration
      **settings (dict): Settings configured in .ini file

    Returns:
      obj: a Pyramid WSGI application
    """

    # plugins
    plugins = get_plugins(settings)

    # config
    for priority in sorted(plugins, reverse=True):
        settings.update(plugins[priority]['settings'])
    settings = replace_environment_vars(settings)
    config = Configurator(settings=settings)

    # db
    Tdb._db = settings['tryton.database']
    Tdb._company = settings['tryton.company']
    Tdb._user = settings['tryton.user']
    Tdb._configfile = settings['tryton.configfile']
    Tdb.init()

    # session
    config.set_session_factory(factory=session_factory_from_settings(settings))

    # policies
    config.set_authorization_policy(policy=ACLAuthorizationPolicy())
    config.set_authentication_policy(
        policy=AuthTktAuthenticationPolicy(
            secret=settings['authentication.secret'],
            hashalg='sha512',
            callback=WebUser.groupfinder
        )
    )
    config.set_default_permission('administrator')

    # subscribers
    config.add_subscriber(
        subscriber='.config.add_templates',
        iface='pyramid.events.BeforeRender'
    )
    config.add_subscriber(
        subscriber='.config.add_helpers',
        iface='pyramid.events.BeforeRender'
    )
    config.add_subscriber(
        subscriber='.config.add_locale',
        iface='pyramid.events.NewRequest'
    )
    if settings['env'] == 'development':
        config.add_subscriber(
            subscriber='.config.debug_request',
            iface='pyramid.events.NewRequest'
        )

    # request methods
    config.add_request_method(
        callable=WebUser.current_web_user,
        name='user',
        reify=True
    )

    config.commit()

    # logging
    for priority in sorted(plugins):
        fileConfig(
            plugins[priority]['path'] + '/' + settings['env'] + '.ini',
            disable_existing_loggers=False
        )

    # webfrontend
    api_in_web = False
    if settings['service'] == 'portal':
        # root factory
        config.set_root_factory(factory=WebRootFactory)
        # resources
        config.include('.resources.include_web_resources')
        for priority in sorted(plugins):
            config.include(plugins[priority]['name']+'.include_web_resources')
        # views
        for priority in sorted(plugins, reverse=True):
            config.include(plugins[priority]['name'] + '.include_web_views')
        config.include('.config.include_web_views')

        if api_in_web:
            # modules
            config.include('cornice')
            # views
            for priority in sorted(plugins, reverse=True):
                config.include(
                    plugins[priority]['name'] + '.config.include_api_views',
                    route_prefix='/api'
                )
            config.include('.config.include_api_views', route_prefix='/api')

    # api
    if settings['service'] == 'api':
        # modules
        config.include('cornice')
        # root factory
        config.set_root_factory(factory=ApiRootFactory)
        # views
        for priority in sorted(plugins, reverse=True):
            config.include(plugins[priority]['name'] + '.include_api_views')
        config.include('.config.include_api_views')

    return config.make_wsgi_app()
