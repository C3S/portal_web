# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import logging

from pyramid.httpexceptions import (
    HTTPException,
    HTTPFound
)

log = logging.getLogger(__name__)


class ViewBase(object):

    def __init__(self, context, request):
        self._formcontroller = {}
        self.request = request
        self.context = context
        self.response = {}
        self.cleanup_forms()
        log.debug(self.context)

    def process_forms(self):
        for name, controller in self._formcontroller.iteritems():
            _response = controller.process(self.context, self.request)
            if isinstance(_response, HTTPException):
                return _response
            self.response.update(_response)
        return self.response

    def register_form(self, controller, name=None, persistent=False):
        if self.request.path.startswith('/static'):
            return
        _name = name or controller.__name__

        # ensure existence of session key
        if 'forms' not in self.request.session:
            self.request.session['forms'] = {}
        _forms = self.request.session['forms']

        # initialize form
        if _name not in _forms:
            _forms[_name] = controller(name=_name, persistent=persistent)

        # register form
        self._formcontroller[_name] = _forms[_name]

    def cleanup_forms(self):
        """
        Reset form, if not persistent and user left the controller flow
        """
        _forms = self.request.session.get('forms', {})
        current_form = self.request.params.get('__formid__', '')
        forms_to_delete = []
        for form_name in _forms:
            if not _forms[form_name].persistent and form_name != current_form:
                forms_to_delete.append(form_name)
        for form_name in forms_to_delete:
            del _forms[form_name]

    def redirect(self, resource, *args, **kwargs):
        if isinstance(resource, str):
            return HTTPFound(location=resource, **kwargs)
        else:
            return HTTPFound(
                self.request.resource_path(resource(self.request), *args),
                **kwargs
            )
        return {}
