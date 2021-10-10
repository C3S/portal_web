# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

from collections import OrderedDict
import logging

from pyramid.httpexceptions import (
    HTTPException,
    HTTPFound
)

from ..resources import ResourceBase


log = logging.getLogger(__name__)


class ViewBase(object):
    """
    The ViewBase class is convenience for form handling

    * process_forms processes registered forms
    * register_forms registers forms ;-)
    * cleanup_forms removes persisted session information
    * redirect sends users elsewhere
    """

    def __init__(self, context, request):
        self._formcontroller = OrderedDict()
        self.request = request
        self.context = context
        self.response = {}
        self.cleanup_forms()

    def process_forms(self, data={}):
        for name, controller in self._formcontroller.items():
            for key in data:
                setattr(self.context, key, data[key])
            _response = controller.process(self.context, self.request)
            if isinstance(_response, HTTPException):
                return _response
            self.response.update(_response)
        return self.response

    def register_form(self, controller, name=None, persistent=False):
        """
        Adds a form (i.e. controller) to a session, remembers it
        """

        # catch edge case...
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

    def redirect(self, resource='', *args, **kwargs):
        if isinstance(resource, str):
            path = self.request.resource_path(self.context, resource, *args)
        elif isinstance(resource, ResourceBase):
            path = self.request.resource_path(resource, *args)
        elif isinstance(resource, type) and issubclass(resource, ResourceBase):
            path = self.request.resource_path(resource(self.request), *args)
        assert path
        return HTTPFound(path, **kwargs)
