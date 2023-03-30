# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

"""
View Base Tests
"""

import pytest

from pyramid.httpexceptions import (
    exception_response,
    HTTPFound,
    HTTPNotFound,
)

from ....views import ViewBase
from ....resources import ResourceBase


class FormControllerMock():
    """
    FormController mock
    """
    __name__ = "formcontrollermock"

    def __init__(self, name='mock', persistent=False):
        self.name = name
        self.persistent = persistent

    def process(self, request, context):
        return {self.name: True}


class FormControllerMockHTTPException():
    """
    FormController mock with exception
    """
    __name__ = "formcontrollermock"

    def __init__(self, name='mock', persistent=False):
        self.name = name
        self.persistent = persistent

    def process(self, request, context):
        return exception_response(404)


@pytest.fixture
def viewbase(pyramid):
    return ViewBase(pyramid.resource, pyramid.request)


class TestViewBase:

    def test_viewbase(self, pyramid):
        """
        Assemble a ViewBase
        """
        viewbase = ViewBase(pyramid.resource, pyramid.request)
        assert viewbase is not None

    def test_process_form_exception(self, viewbase):
        """
        Test proces form exception
        """
        viewbase.register_form(FormControllerMockHTTPException, name="bla")
        result = viewbase.process_forms()
        assert isinstance(result, HTTPNotFound)

    def test_process_form_processed(self, viewbase):
        """
        Test process form processed
        """
        viewbase.register_form(FormControllerMock, name="bla")
        viewbase.register_form(FormControllerMock, name="blupp")
        result = viewbase.process_forms()
        assert "bla" in result.keys()
        assert "blupp" in result.keys()

    def test_redirect_str(self, viewbase):
        """
        Test redirect str
        """
        result = viewbase.redirect('/foo')
        assert isinstance(result, HTTPFound)

    def test_redirect_resource_instance(self, pyramid, viewbase):
        """
        Test redirect resource instance
        """
        mock_resource = ResourceBase(pyramid.request)
        result = viewbase.redirect(mock_resource, "foo")
        assert isinstance(result, HTTPFound)

    def test_redirect_resource_class(self, viewbase):
        """
        Test redirect resource class
        """
        mock_resource = ResourceBase
        result = viewbase.redirect(mock_resource, "foo")
        assert isinstance(result, HTTPFound)

    def test_registerform_staticpath(self, pyramid):
        """
        Test registerform static path
        """
        pyramid.request.path = "/static/foo/barform"
        viewbase = ViewBase(pyramid.resource, pyramid.request)
        viewbase.register_form(FormControllerMock)
        assert viewbase is not None
        assert viewbase._formcontroller == {}

    def test_registerform(self, viewbase):
        """
        Test register form
        """
        viewbase.register_form(FormControllerMock, name="bla")
        assert viewbase is not None
        assert "bla" in viewbase._formcontroller

    def test_cleanup_form_persistence(self, pyramid):
        """
        Test persistence
        """
        pyramid.request.session['forms'] = {
            "id1": FormControllerMock(persistent=True),
        }
        viewbase = ViewBase(pyramid.resource, pyramid.request)
        assert viewbase
        assert "id1" in pyramid.request.session['forms']

    def test_cleanup_form_deletion(self, pyramid):
        """
        Test deletion
        """
        pyramid.request.session['forms'] = {
            "id2": FormControllerMock(persistent=False),
            "id3": FormControllerMock(persistent=False),
        }
        viewbase = ViewBase(pyramid.resource, pyramid.request)
        assert viewbase
        assert "id2" not in pyramid.request.session['forms']
        assert "id3" not in pyramid.request.session['forms']

    def test_cleanup_form_dontdeleteforminflow(self, pyramid):
        """
        Simulate active flow
        """
        pyramid.request.session['forms'] = {
            "id2": FormControllerMock(persistent=False),
            "id3": FormControllerMock(persistent=False),
        }
        pyramid.request.params['__formid__'] = "id3"
        viewbase = ViewBase(pyramid.resource, pyramid.request)
        assert viewbase
        assert "id2" not in pyramid.request.session['forms']
        assert "id3" in pyramid.request.session['forms']
