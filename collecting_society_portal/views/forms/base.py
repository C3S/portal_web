# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

from abc import ABCMeta, abstractmethod
import logging

from pyramid.httpexceptions import HTTPFound
import colander
import deform

log = logging.getLogger(__name__)


class FormController(object):
    __metaclass__ = ABCMeta
    __stage__ = None

    def __init__(self, name=None, stage=None, appstruct=None,
                 context=None, request=None, response=None):
        self._name = name or self.__class__.__name__
        self._form = None
        self._data = {}
        self.stage = stage or self.__stage__
        self.appstruct = appstruct
        self.context = context
        self.request = request
        self.response = response or {}
        self.validationfailure = None

    def __getstate__(self):
        return {
            '__stage__': self.__stage__,
            '_name': self._name,
            '_data': self._data,
            'stage': self.stage,
            'appstruct': self.appstruct
        }

    def __setstate__(self, state):
        self.__stage__ = state['__stage__']
        self._name = state['_name']
        self._form = None
        self._data = state['_data']
        self.stage = state['stage']
        self.appstruct = state['appstruct']
        self.context = None
        self.request = None
        self.response = {}

    @property
    def name(self):
        return self._name

    @property
    def form(self):
        return self._form

    @form.setter
    def form(self, form, render=True):
        self._form = form
        if self._form.formid == 'deform':
            self._form.formid = self.name
        if render:
            self.response = {self.name: self._form.render()}

    @property
    def data(self):
        return self._data

    def render(self, appstruct={}, form=None):
        if form is None:
            form = self.form
        self.response = {self.name: form.render(appstruct=appstruct)}

    def process(self, context, request):
        self.context = context
        self.request = request
        return self.controller()

    @abstractmethod
    def controller(self):
        pass

    # --- Conditions ----------------------------------------------------------

    def submitted(self, button=None):
        data = self.request.POST or self.request.GET
        if not data:
            return False
        if '__formid__' in data and self._form.formid == data['__formid__']:
            if button:
                return button in data
            return True
        return False

    def valid(self):
        return self.validationfailure is None

    # --- Actions -------------------------------------------------------------

    def redirect(self, resource, *args, **kwargs):
        if isinstance(resource, str):
            self.response = HTTPFound(location=resource, **kwargs)
        else:
            self.response = HTTPFound(
                self.request.resource_path(resource(self.request), *args),
                **kwargs
            )
        self.remove()

    def validate(self):
        self.appstruct, self.validationfailure = None, None
        try:
            data = self.request.POST.items() or self.request.GET.items()
            self.appstruct = self.form.validate(data)
            self.response = {self.name: self.form.render()}
            return True
        except deform.ValidationFailure as e:
            self.validationfailure = e
            self.response = {self.name: self.validationfailure.render()}
        return False

    def clean(self):
        self._form = None
        self._data = {}
        self.appstruct = None
        self.context = None
        self.stage = self.__stage__
        self.validationfailure = None

    def remove(self):
        if self.name in self.request.session['forms']:
            del self.request.session['forms'][self.name]


@colander.deferred
def deferred_file_upload_widget(node, kw):
    request = kw.get('request')
    session = request.session
    if 'file_upload' not in session:
        class MemoryTmpStore(dict):
            def preview_url(self, name):
                return None
        session['file_upload'] = MemoryTmpStore()
    widget = deform.widget.FileUploadWidget(session['file_upload'])
    return widget
