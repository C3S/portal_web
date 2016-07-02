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
        _name = name or controller.__module__

        # ensure existence of session key
        if 'forms' not in self.request.session:
            self.request.session['forms'] = {}
        _forms = self.request.session['forms']

        # reset form, if not persistent and user left the form controller flow
        if not persistent and _name in _forms:
            # name in params
            _pname = ""
            if '__formid__' in self.request.params:
                _pname = self.request.params['__formid__']
            # name in session
            _sname = _forms[_name].name
            # comparison of params name and session name
            if _pname != _sname:
                del _forms[_name]

        # initialize form
        if _name not in _forms:
            _forms[_name] = controller()

        # register form
        self._formcontroller[_name] = _forms[_name]

    def redirect(self, resource, *args, **kwargs):
        if isinstance(resource, str):
            return HTTPFound(location=resource, **kwargs)
        else:
            return HTTPFound(
                self.request.resource_path(resource(self.request), *args),
                **kwargs
            )
        return {}
