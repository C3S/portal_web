# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import os
import logging
from pkgutil import iter_modules
import ConfigParser

from pyramid.renderers import get_renderer
from pyramid.i18n import (
    default_locale_negotiator,
)

from . import helpers

log = logging.getLogger(__name__)


def include_web_views(config):
    config.add_static_view('static/portal', 'static', cache_max_age=3600)
    config.add_static_view(
        'static/deform', 'deform:static', cache_max_age=3600
    )
    config.scan(ignore='.views.api')


def include_api_views(config):
    settings = config.get_settings()

    # views
    if settings['env'] == 'development':
        config.add_static_view('static/portal', 'static', cache_max_age=3600)
    config.scan('.views.api')


def replace_environment_vars(settings):
    """
    Substitues placeholder with environment variables in a settings dictionary.

    Args:
      settings: Settings configured in .ini file

    Returns:
      dict: updated settings
    """
    return dict(
        (key, os.path.expandvars(value)) for key, value in settings.iteritems()
    )


def get_plugins(settings):
    """
    Fetches plugins based on module name pattern matching.

    Args:
      settings: Settings configured in .ini file

    Returns:
      dict: priority of plugin as the key; name, settings and path of plugins
        as values
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
    base = get_renderer('templates/base.pt').implementation()
    frontend = get_renderer('templates/frontend.pt').implementation()
    backend = get_renderer('templates/backend.pt').implementation()
    macros = get_renderer('templates/macros.pt').implementation()
    event.update({
        'base': base,
        'frontend': frontend,
        'backend': backend,
        'm': macros
    })


def add_helpers(event):
    event['h'] = helpers


def add_locale(event):
    """
    add a cookie for the language to display (fallback to english).
    """
    LANGUAGE_MAPPING = {
        'de': 'de',
        'en': 'en',
    }

    locale = default_locale_negotiator(event.request)
    if locale is None:
        # default language
        locale = 'en'
        # check browser for language
        browser = event.request.accept_language
        if browser:
            locale_matched = browser.best_match(LANGUAGE_MAPPING, 'en')
            log.debug(
                (
                    "creating cookie for locale:\n"
                    "- locale of browser: %s\n"
                    "- locale matched: %s"
                ) % (
                    browser, locale_matched
                )
            )
            locale = LANGUAGE_MAPPING.get(locale_matched)
        # set cookie
        event.request.response.set_cookie('_LOCALE_', value=locale)

    event.request._LOCALE_ = locale


def debug_request(event):
    p = event.request.path
    if not p.startswith('/static/') and not p.startswith('/_debug_toolbar/'):
        log.debug("ENVIRON:\n %s" % event.request.environ)
