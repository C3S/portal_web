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
        log.debug(self.context)

    def process_forms(self):
        response = {}
        for name, controller in self._formcontroller.iteritems():
            _response = controller.process(self.context, self.request)
            if isinstance(_response, HTTPException):
                return _response
            response.update(_response)
        return response

    def register_form(self, controller, name=None):
        _name = name or controller.__module__
        if 'forms' not in self.request.session:
            self.request.session['forms'] = {}
        if _name not in self.request.session['forms']:
            self.request.session['forms'][_name] = controller()
        self._formcontroller[_name] = self.request.session['forms'][_name]

    def redirect(self, resource, *args, **kwargs):
        if isinstance(resource, str):
            return HTTPFound(location=resource, **kwargs)
        else:
            return HTTPFound(
                self.request.resource_path(resource(self.request), *args),
                **kwargs
            )
        return {}
