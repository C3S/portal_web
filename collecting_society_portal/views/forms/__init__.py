# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

# base
from .base import (
    FormController,
    deferred_file_upload_widget
)

# form controller
from .login_web_user import LoginWebuser
from .register_web_user import RegisterWebuser

# deform translator
from pkg_resources import resource_filename
from pyramid.threadlocal import get_current_request
from pyramid.i18n import get_localizer
import deform


# deform translator
def translator(term):
    return get_localizer(get_current_request()).translate(term)
custom_templates = resource_filename(
    'collecting_society_portal',
    'templates/deform'
)
deform_templates = resource_filename('deform', 'templates')
zpt_renderer = deform.ZPTRendererFactory(
    [custom_templates, deform_templates],
    translator=translator
)
deform.Form.set_default_renderer(zpt_renderer)
