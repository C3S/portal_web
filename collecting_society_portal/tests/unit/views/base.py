# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

"""
Dictionary Merge Tests
"""
# from pyramid.httpexceptions import HTTPException
from pyramid.httpexceptions import (
    exception_response,
    HTTPException
)
from pyramid.testing import (
    DummyRequest,
    DummyResource
)


from ...base import UnitTestBase

from ....views import ViewBase
from ....resources import ResourceBase


class FormControllerMock():
    __name__ = "formcontrollermock"

    def __init__(self, name='mock', persistent=False):
        self.name = name
        self.persistent = persistent

    def process(self, request, context):
        return {self.name: True}


class FormControllerMockHTTPException():
    __name__ = "formcontrollermock"

    def __init__(self, name='mock', persistent=False):
        self.name = name
        self.persistent = persistent

    def process(self, request, context):
        # return HTTPException(404)
        return exception_response(404)


class TestViewBase(UnitTestBase):

    def setUp(self):
        # self.controller =
        self.request = DummyRequest()
        self.context = DummyResource()
        self.request.session = {
        }
        # self.context = self.request.context
        # import pdb; pdb.set_trace()

    def test_viewbase(self):
        """
        Assemble a ViewBase
        """
        my_viewbase = ViewBase(self.context, self.request)
        assert(my_viewbase is not None)

    def test_process_form_exception(self):
        my_viewbase = ViewBase(self.context, self.request)
        my_viewbase.register_form(
            FormControllerMockHTTPException, name="bla")
        # my_viewbase.register_form(
        #     FormControllerMockHTTPException, name="blupp")
        result = my_viewbase.process_forms()

        from pyramid.httpexceptions import HTTPNotFound
        self.assertIsInstance(result, HTTPNotFound)

    def test_process_form_processed(self):
        my_viewbase = ViewBase(self.context, self.request)
        my_viewbase.register_form(FormControllerMock, name="bla")
        my_viewbase.register_form(FormControllerMock, name="blupp")
        result = my_viewbase.process_forms()
        self.assertIn("bla", result.keys())
        self.assertIn("blupp", result.keys())

    def test_redirect_str(self):
        my_viewbase = ViewBase(self.context, self.request)
        result = my_viewbase.redirect('/foo')
        self.assertIsInstance(result, HTTPException)

    def test_redirect_resource(self):
        my_viewbase = ViewBase(self.context, self.request)
        mock_resource = DummyResource
        # self.request.resource_path = '/foo
        result = my_viewbase.redirect(mock_resource, "foo")
        # self.assertIsInstance(result, HTTPException)
        self.assertNotIsInstance(result, ResourceBase)

    def test_registerform_staticpath(self):
        '''
        foo
        '''
        # self.request = DummyRequest(path="/static/foo/barform")
        self.request.path = "/static/foo/barform"
        my_viewbase = ViewBase(self.context, self.request)

        my_viewbase.register_form(FormControllerMock)
        assert(my_viewbase is not None)
        self.assertEqual({}, my_viewbase._formcontroller)
        self.assertFalse(my_viewbase._formcontroller)

    def test_registerform(self):

        my_viewbase = ViewBase(self.context, self.request)

        my_viewbase.register_form(FormControllerMock, name="bla")
        assert(my_viewbase is not None)
        self.assertIn("bla", my_viewbase._formcontroller)

    def test_cleanup_form_persistence(self):
        """
        Test persistence
        """

        self.request.session['forms'] = {
            "id1": FormControllerMock(persistent=True),
            # "id2": FormControllerMock(param=False),
            # "id3": FormControllerMock(param=False),
        }
        my_viewbase = ViewBase(self.context, self.request)
        my_viewbase
        self.assertIn("id1", self.request.session['forms'])
        # self.assertNotIn("id2", self.request.session['forms'])
        # self.assertNotIn("id3", self.request.session['forms'])

    def test_cleanup_form_deletion(self):
        """
        Test deletion
        """

        self.request.session['forms'] = {
            "id2": FormControllerMock(persistent=False),
            "id3": FormControllerMock(persistent=False),
        }
        my_viewbase = ViewBase(self.context, self.request)
        my_viewbase
        # self.assertIn("id1", self.request.session['forms'])
        self.assertNotIn("id2", self.request.session['forms'])
        self.assertNotIn("id3", self.request.session['forms'])

    def test_cleanup_form_dontdeleteforminflow(self):
        """
        Simulate active flow
        """

        self.request.session['forms'] = {
            "id2": FormControllerMock(persistent=False),
            "id3": FormControllerMock(persistent=False),
        }
        self.request.params['__formid__'] = "id3"
        my_viewbase = ViewBase(self.context, self.request)
        my_viewbase
        self.assertNotIn("id2", self.request.session['forms'])
        self.assertIn("id3", self.request.session['forms'])
