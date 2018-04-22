# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import os
import shutil
import glob
import tempfile
# from tempfile import NamedTemporaryFile
import time

from abc import ABCMeta, abstractmethod
import logging

from pyramid.httpexceptions import HTTPFound
import colander
import deform

log = logging.getLogger(__name__)


class FormController(object):
    """
    Abstract class for form handling
    """
    __metaclass__ = ABCMeta
    __stage__ = None

    def __init__(self, name=None, stage=None, persistent=False, appstruct=None,
                 context=None, request=None, response=None):
        self._name = name or self.__class__.__name__
        self._form = None
        self._data = {}  # aggregates several appstructs, dep. on form design
        self.persistent = persistent  # store in session?
        self.stage = stage or self.__stage__
        self.appstruct = appstruct or {}
        self.context = context
        self.request = request
        self.response = response or {}
        self.validationfailure = None

    def __getstate__(self):
        return {
            '__stage__': self.__stage__,
            '_name': self._name,
            '_data': self._data,
            'persistent': self.persistent,
            'stage': self.stage,
            'appstruct': self.appstruct
        }

    def __setstate__(self, state):
        self.__stage__ = state['__stage__']
        self._name = state['_name']
        self._form = None
        self._data = state['_data']
        self.persistent = state['persistent']
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
        """
        some kind of appstruct
        """
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
        """
        overwrite this with your form logic!
        (if form is submitted and ... then ...)
        """
        pass  # pragma: no cover

    # --- Conditions ----------------------------------------------------------

    def submitted(self, button=None):
        """
        check to see if your form was submitted (by special button?)
        """
        data = self.request.POST or self.request.GET
        if not data:
            return False
        if '__formid__' in data and self._form.formid == data['__formid__']:
            if button:
                return button in data
            return True
        return False

    def valid(self):
        """
        check if form did validate on last validation
        """
        return self.validationfailure is None

    # --- Actions -------------------------------------------------------------

    def redirect(self, resource, *args, **kwargs):
        """
        return user to other place by str or resource,
        removes form from session
        """
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
        """
        reset the form
        """
        self._form = None
        self._data = {}
        self.appstruct = None
        self.context = None
        self.stage = self.__stage__
        self.validationfailure = None

    def remove(self):
        """
        no longer persist form in session
        """
        if self.name in self.request.session['forms']:
            del self.request.session['forms'][self.name]


class MemoryTmpStore(dict):
    def preview_url(self, name):
        return None


class TmpFile(object):

    def __init__(self, source, *args, **kwargs):
        self.file = tempfile.NamedTemporaryFile(*args, **kwargs)
        shutil.copyfileobj(source, self)

    def __getstate__(self):
        try:
            return self.name
        except:
            pass
        return None

    def __setstate__(self, name):
        self.file = None
        if name and os.path.isfile(name):
            self.file = open(name, 'r')

    def __getattr__(self, attr):
        return getattr(self.file, attr)

    def __iter__(self):
        return iter(self.file)

    def delete(self):
        file = self.name
        if file and os.path.isfile(file):
            os.unlink(file)


class FileTmpStore(dict):

    def __init__(self, path=None, timeout=0):
        self.path = path
        self.timeout = timeout
        self.files = {}
        self.clear_tmpfiles()

    def clear_tmpfiles(self):
        if not self.timeout:
            return
        path = os.path.join(self.path, 'tmp*')
        for tmpfile in glob.glob(path):
            created = os.stat(tmpfile).st_mtime
            now = time.time()
            if created < now - self.timeout:
                os.unlink(tmpfile)

    def __setitem__(self, name, cstruct):
        tmpfile = TmpFile(source=cstruct['fp'], dir=self.path, delete=False)
        cstruct['fp'].close()
        cstruct['fp'] = tmpfile
        super(FileTmpStore, self).__setitem__(name, cstruct)

    def preview_url(self, name):
        return None


@colander.deferred
def deferred_file_upload_widget(node, kw):
    request = kw.get('request')
    session = request.session
    basepath = request.registry.settings.get('session.data_dir', '/tmp')
    path = os.path.join(basepath, 'file_tmp_store')
    timeout = int(request.registry.settings.get('session.file_expires', 0))
    if not os.path.isdir(path):
        os.makedirs(path)
    if 'file_upload' not in session:
        session['file_upload'] = FileTmpStore(path=path, timeout=timeout)
    widget = deform.widget.FileUploadWidget(session['file_upload'])
    return widget
