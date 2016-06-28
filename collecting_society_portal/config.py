# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

"""
Helper functions for the creation of the pyramid app.
"""

import os
import logging
from pkgutil import iter_modules
import ConfigParser

from pyramid.httpexceptions import (
    HTTPFound,
    HTTPNotFound
)
from pyramid.renderers import get_renderer

from . import helpers

log = logging.getLogger(__name__)


def replace_environment_vars(settings):
    """
    Substitues placeholders in app settings with environment variables.

    Values in the app settings with the syntax `${ENVIRONMENT_VARIABLE}` are
    substituted with the respective value of the key ENVIRONMENT_VARIABLE in
    the environment variables.

    Args:
        settings (dict): Parsed [app:main] section of .ini file.

    Returns:
        dict: substituted settings.

    Examples:
        >>> import os
        >>> os.environ['PYRAMID_SERVICE'] = 'portal'
        >>> settings = { 'service': '${PYRAMID_SERVICE}' }
        >>> print(replace_environment_vars(settings))
        { 'service' = 'portal' }
    """
    return dict(
        (key, os.path.expandvars(value)) for key, value in settings.iteritems()
    )


def get_plugins(settings):
    """
    Fetches plugin settings based on module name pattern matching.

    The module name pattern needs to be configured in the portal app settings
    as key `plugins.pattern`. All modules starting with this pattern will be
    treated as portal plugins.

    Note:
        Dots in module names get substituted by an underscore.

    Args:
        settings (dict): Parsed [app:main] section of .ini file.

    Returns:
        dict: plugin settings.

    Examples:
        >>> settings = { 'plugins.pattern': 'collecting_society_portal_' }
        >>> print(get_plugins(settings))
        {
            200: {
                'path': '/ado/src/collecting_society.portal.imp',
                'name': 'collecting_society_portal_imp',
                'settings': {}
            },
            100: {
                'path': '/ado/src/collecting_society.portal.creative',
                'name': 'collecting_society_portal_creative',
                'settings': {}
            }
        }
    """
    plugins = {}
    modules = [
        {'name': name, 'path': imp.path} for imp, name, _ in iter_modules()
        if name.startswith(settings['plugins.pattern'])
    ]
    config = ConfigParser.ConfigParser()
    for plugin in modules:
        settings_path = plugin['path'] + '/' + settings['env'] + '.ini'
        config.read(settings_path)
        plugin_settings = dict(config.items('plugin:main'))
        if 'plugin.priority' not in plugin_settings:
            raise KeyError("'plugin.priority' missing in " + settings_path)
        priority = int(plugin_settings['plugin.priority'])
        del plugin_settings['plugin.priority']
        plugins[priority] = {
            'name': plugin['name'],
            'settings': plugin_settings,
            'path': plugin['path']
        }
    return plugins


def add_templates(event):
    """
    Adds base templates and macros as top-level name in temlating system.

    Args:
        event (pyramid.events.BeforeRender): BeforeRender event.

    Returns:
        None.
    """
    event.update({
        'base':     get_renderer('templates/base.pt').implementation(),
        'frontend': get_renderer('templates/frontend.pt').implementation(),
        'backend':  get_renderer('templates/backend.pt').implementation(),
        'm':        get_renderer('templates/macros.pt').implementation()
    })


def add_helpers(event):
    """
    Adds helper functions as top-level name in temlating system.

    Args:
        event (pyramid.events.BeforeRender): BeforeRender event.

    Returns:
        None.
    """
    event['h'] = helpers


def add_locale(event):
    """
    Sets the language of the app.

    Considers several sources in the following, descending order:

    1. request: manual choice of language using GET parameter `_LOCALE_`
    2. cookie: formerly chosen or detected language using cookie `_LOCALE_`
    3. browser: browser language using HTTP header `Accept-Language`
    4. default: en

    The chosen or detected language will be saved in a cookie `_LOCALE_`.

    Args:
        event (pyramid.events.NewRequest): NewRequest event.

    Returns:
        None.
    """
    LANGUAGE_MAPPING = {
        'de': 'de',
        'en': 'en',
        'es': 'es',
    }
    default = 'en'

    # default locale
    current = default

    # cookie locale
    cookie = event.request.cookies.get('_LOCALE_')
    if cookie:
        event.request._LOCALE_ = cookie

    # check browser for language, if no cookie present
    browser = event.request.accept_language
    if not cookie and browser:
        match = browser.best_match(LANGUAGE_MAPPING, default)
        current = LANGUAGE_MAPPING.get(match)
        event.request._LOCALE_ = current
        event.request.response.set_cookie('_LOCALE_', value=current)

    # language request
    request = event.request.params.get('_LOCALE_')
    if request and request in LANGUAGE_MAPPING:
        current = LANGUAGE_MAPPING.get(request)
        event.request._LOCALE_ = current
        event.request.response = HTTPFound(location=event.request.path_url)
        event.request.response.set_cookie('_LOCALE_', value=current)


def notfound(request):
    """
    Not Found view (404 Error).

    Args:
        request (pyramid.request): Current request.

    Returns:
        pyramid.httpexceptions.HTTPNotFound: 404 Response.
    """
    return HTTPNotFound()


def debug_request(event):
    """
    Prints request environment to debug log.

    Args:
        event (pyramid.events.NewRequest): NewRequest event.

    Returns:
        None.
    """
    p = event.request.path
    if not p.startswith('/static/') and not p.startswith('/_debug_toolbar/'):
        log.debug("REQUEST:\n %s" % event.request)


class Environment(object):
    """
    View predicate factory for restricting views to environments.

    Args:
        val (str): value for comparison.
        config (pyramid.config.Configurator): App config.

    Classattributes:
        phash (str): hash for view predicate.

    Attributes:
        val (str): value for comparison.
    """
    def __init__(self, val, config):
        self.val = val

    def text(self):
        return 'environment = %s' % (self.val,)

    phash = text

    def __call__(self, context, request):
        '''
        Compares the value of the key `env` in registry settings with the value
        of the view predicate key `environment`.

        Args:
            context (object): Current resource.
            request (pyramid.request): Current request.

        Returns:
            True if val is equal to the current environment, False otherwise.
        '''
        return request.registry.settings['env'] == self.val
