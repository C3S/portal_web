# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

from pkg_resources import resource_filename
from pyramid.threadlocal import get_current_request
from pyramid.i18n import get_localizer
import deform

from .base import (
    FormController,
    deferred_file_upload_widget
)
from .login_web_user import LoginWebuser
from .register_web_user import RegisterWebuser
from ...config import get_plugins


# deform default renderer
def get_translator(term):
    return get_localizer(get_current_request()).translate(term)


def get_templates():
    templates = []
    plugins = get_plugins()
    for priority in sorted(plugins):
        templates.append(
            resource_filename(plugins[priority]['name'], 'templates/deform'))
    templates += [
        resource_filename('collecting_society_portal', 'templates/deform'),
        resource_filename('deform', 'templates')
    ]
    return templates


zpt_renderer = deform.ZPTRendererFactory(
    get_templates(), translator=get_translator)
deform.Form.set_default_renderer(zpt_renderer)
