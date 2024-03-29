# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

from inspect import signature
import deform
import sys
import os

from pyramid import testing
from paste.deploy.loadwsgi import appconfig

from ....config import (
    get_plugins,
    replace_environment_vars,
    web_user,
    party,
    user,
    roles,
)
from ....views.forms.datatables import DatatableSequenceWidget
from .elements import (  # noqa: F401
    TextInputWidgetElement,
    TextAreaWidgetElement,
    HiddenWidgetElement,
    PasswordWidgetElement,
    CheckedPasswordWidgetElement,
    RadioChoiceWidgetElement,
    CheckboxWidgetElement,
    CheckboxChoiceWidgetElement,
    DateInputWidgetElement,
    FileUploadWidgetElement,
    DatatableSequenceWidgetElement,
    ButtonElement,
)

__all__ = ['DeformFormObject']


def settings():
    """
    Provides parsed pyramid settings (plugins combined, envvars substituted).
    """
    environment = 'testing'
    settings = appconfig(
        'config:' + os.path.join(
            os.path.dirname(__file__), '..', '..', '..', '..',
            f'{environment}.ini'
        )
    )
    plugins = get_plugins(settings, environment)
    for priority in sorted(plugins, reverse=True):
        settings.update(plugins[priority]['settings'])
    settings = replace_environment_vars(settings)
    return settings


class DeformFormObject(object):

    def __init__(self, browser, form, formid, userid=None):
        if callable(form):
            sig = signature(form)
            if sig.parameters.get('request'):
                request = testing.DummyRequest()
                config = testing.setUp(request=request, settings=settings())
                if userid:
                    config.testing_securitypolicy(userid)
                    request.web_user = web_user(request)
                    request.party = party(request)
                    request.user = user(request)
                    request.roles = roles(request)
                form = form(request)
            else:
                form = form()
        self._browser = browser
        self._form = form
        self._formid = formid
        self._parse_form(self._form)

    def _parse_form(self, form):
        # parse fields
        for child in form.children:
            if not isinstance(child, deform.field.Field):
                raise NotImplementedError('parser not implemented')
            self._parse_field(child)
        # parse buttons
        for button in self._form.buttons:
            locator = self._formid + button.name
            setattr(self, button.name,
                    ButtonElement(self._browser, locator,
                                  name=button.name, formid=self._formid))

    def _parse_field(self, field):
        if isinstance(field.widget, (deform.widget.TextInputWidget,
                                     deform.widget.TextAreaWidget,
                                     deform.widget.HiddenWidget,
                                     deform.widget.PasswordWidget,
                                     deform.widget.CheckboxWidget,
                                     deform.widget.CheckedPasswordWidget,
                                     deform.widget.RadioChoiceWidget,
                                     deform.widget.DateInputWidget,
                                     deform.widget.FileUploadWidget,
                                     DatatableSequenceWidget,
                                     deform.widget.RadioChoiceWidget,
                                     deform.widget.CheckboxChoiceWidget)):
            cls = getattr(
                sys.modules[__name__],
                field.widget.__class__.__name__ + 'Element'
            )
            attr = field.oid.replace("-", "_")
            setattr(self, attr, cls(self._browser, field.oid))
        else:
            raise NotImplementedError(
                'parser not implemented: ' + field.widget.__class__.__name__)
