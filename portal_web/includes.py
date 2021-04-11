# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

"""
Functions to include resources/views and register content by the plugin system.

The following functions are called by convention on app creation:

- web_resources
- web_registry
- web_views
- api_views
"""

from .resources import (
    BackendResource,
    FrontendResource,
    DebugResource
)


def web_resources(config):
    '''
    Extends the resource tree for the web service.

    Note:
        The function is called by the plugin system, when the app is created.

    Args:
        config (pyramid.config.Configurator): App config.

    Returns:
        None.
    '''
    settings = config.get_settings()
    if settings['env'] == 'development':
        BackendResource.add_child(DebugResource)
        FrontendResource.add_child(DebugResource)


def web_registry(config):
    '''
    Extends the registry for content elements for the web service.

    Note:
        The function is called by the plugin system, when the app is created.

    Args:
        config (pyramid.config.Configurator): App config.

    Returns:
        None.
    '''
    pass


def web_views(config):
    '''
    Adds the views for the web service.

    Note:
        The function is called by the plugin system, when the app is created.

    Args:
        config (pyramid.config.Configurator): App config.

    Returns:
        None.
    '''
    config.add_static_view(
        'static/portal', 'static', cache_max_age=3600
    )
    config.add_static_view(
        'static/deform', 'deform:static', cache_max_age=3600
    )
    config.scan(ignore=['.views.api', '.tests'])


def api_views(config):
    '''
    Adds the views for the api service.

    Note:
        The function is called by the plugin system, when the app is created.

    Args:
        config (pyramid.config.Configurator): App config.

    Returns:
        None.
    '''
    settings = config.get_settings()
    if settings['env'] == 'development':
        config.add_static_view(
            'static/portal', 'static', cache_max_age=3600
        )
    config.scan('.views.api')
