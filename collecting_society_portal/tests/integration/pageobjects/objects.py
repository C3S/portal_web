# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import deform
import sys

from .elements import (
    TextInputWidgetElement,
    TextAreaWidgetElement,
    HiddenWidgetElement,
    PasswordWidgetElement,
    RadioChoiceWidgetElement,
    CheckboxChoiceWidgetElement,
    ButtonElement
)

__all__ = ['DeformFormObject']


class DeformFormObject(object):

    def __init__(self, client, form, formid):
        if not isinstance(form, deform.Form):
            raise TypeError('form is not an instance of deform.Form')
        self._cli = client
        self._form = form
        self._formid = formid
        self._parse_form(self._form)

    def _parse_form(self, form):
        # parse fields
        for child in form.children:
            if not isinstance(child, deform.field.Field):
                raise NotImplementedError(child + ' parser not implemented')
            self._parse_field(child)
        # parse buttons
        for button in self._form.buttons:
            locator = self._formid + button.name
            setattr(self, button.name, ButtonElement(self._cli, locator))

    def _parse_field(self, field):
        if isinstance(field.widget, (deform.widget.TextInputWidget,
                                     deform.widget.TextAreaWidget,
                                     deform.widget.HiddenWidget,
                                     deform.widget.PasswordWidget,
                                     deform.widget.RadioChoiceWidget,
                                     deform.widget.CheckboxChoiceWidget)):
            cls = getattr(
                sys.modules[__name__],
                field.widget.__class__.__name__ + 'Element'
            )
            setattr(self, field.oid, cls(self._cli, field.oid))
        else:
            raise NotImplementedError(field + ' parser not implemented')
