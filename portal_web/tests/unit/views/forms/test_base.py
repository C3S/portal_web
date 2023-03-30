# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

"""
Form Controller Tests
"""

from pyramid.httpexceptions import HTTPFound

from pyramid.testing import DummyResource, DummyRequest

from .....resources import ResourceBase
from .....views.forms.base import FormController


class FormControllerMock(FormController):
    def controller(self):
        return 'controlled'


class DeformFormMockValidating():
    formid = 'my_form_id'

    def validate(self, data):
        return {'foo': 'bar'}

    def render(self, appstruct={}):
        return "<form></form>"


class DeformFormMockNonValidating():
    formid = 'deform'

    def validate(self, data):
        import deform

        e = deform.exception.ValidationFailure(
            'foofield', {}, 'my error')
        e.render = self.render
        raise e

    def render(self):
        return "<form></form>"


class TestFormController:
    """
    FormController test class
    """
    def test_formcontroller_controller(self):
        """
        Test the FormController class
        """
        my_form = FormControllerMock()
        assert my_form

    def test_formcontroller_getstate(self):
        """
        Test the FormController class
        """
        my_form = FormControllerMock()
        res = my_form.__getstate__()
        assert res['_name'] == 'FormControllerMock'
        assert res['persistent'] is False

    def test_formcontroller_setstate(self):
        """
        Test the FormController class
        """
        my_form = FormControllerMock()
        res = my_form.__getstate__()
        assert res['_name'] == 'FormControllerMock'
        assert res['persistent'] is False

        new_state = {
            '_name': 'FormControllerMoo',
            'persistent': True,
            'appstruct': {"foo": "moo"},
            '_data': {},
            '__stage__': None,
            'stage': None}
        my_form.__setstate__(new_state)
        res = my_form.__getstate__()
        assert res['_name'] == 'FormControllerMoo'
        assert res['persistent'] is True

    def test_validate(self):
        """
        Test validation success
        """
        post_dict = {"foo": "bar"}
        request = DummyRequest(post=post_dict)
        context = DummyResource()

        my_deform_form = DeformFormMockValidating()

        my_form = FormControllerMock(
            context=context,
            request=request,
        )
        my_form.form = my_deform_form
        res = my_form.validate()
        assert res is True
        vres = my_form.valid()
        assert vres is True

    def test_validate_not(self):
        """
        Test validation failure
        """
        post_dict = {"foo": "bar"}
        request = DummyRequest(post=post_dict)
        context = DummyResource()

        my_deform_form = DeformFormMockNonValidating()

        my_form = FormControllerMock(
            context=context,
            request=request,
        )
        my_form.form = my_deform_form
        res = my_form.validate()
        assert res is False
        assert my_form.validationfailure.error == 'my error'

    def test_render(self):
        """
        Test render
        """
        post_dict = {"foo": "bar"}
        request = DummyRequest(post=post_dict)
        context = DummyResource()
        request.registry.settings = {'env': 'testing'}

        my_deform_form = DeformFormMockValidating()

        my_form = FormControllerMock(
            context=context,
            request=request,
        )
        my_form.form = my_deform_form
        my_form.render()
        assert 'FormControllerMock' in my_form.response
        assert my_form.response['FormControllerMock'] == '<form></form>'

    def test_process(self):
        """
        Test process forms
        """
        request = DummyRequest()
        context = DummyResource()

        my_deform_form = DeformFormMockValidating()

        my_form = FormControllerMock(
            context=context,
            request=request,
        )
        my_form.form = my_deform_form
        res = my_form.process(context, request)
        assert res == 'controlled'

    def test_data(self):
        """
        Test data
        """
        post_dict = {"foo": "bar"}
        request = DummyRequest(post=post_dict)
        context = DummyResource()

        my_deform_form = DeformFormMockValidating()

        my_form = FormControllerMock(
            context=context,
            request=request,
        )
        my_form.form = my_deform_form
        res = my_form.data
        assert res == {}

    def test_submitted_false(self):
        """
        Test submitted false
        """
        post_dict = {"foo": "bar"}
        request = DummyRequest(post=post_dict)
        context = DummyResource()

        my_deform_form = DeformFormMockValidating()

        my_form = FormControllerMock(
            context=context,
            request=request,
        )
        my_form.form = my_deform_form
        res = my_form.submitted()
        assert res is False

    def test_submitted_false_nodata(self):
        """
        Test submitted false nodata
        """
        post_dict = {}
        request = DummyRequest(post=post_dict)
        context = DummyResource()

        my_deform_form = DeformFormMockValidating()

        my_form = FormControllerMock(
            context=context,
            request=request,
        )
        my_form.form = my_deform_form
        res = my_form.submitted()
        assert res is False

    def test_submitted_true(self):
        """
        Test submitted true
        """
        post_dict = {
            "foo": "bar",
            "__formid__": "my_form_id"
        }
        request = DummyRequest(post=post_dict)
        context = DummyResource()

        my_deform_form = DeformFormMockValidating()

        my_form = FormControllerMock(
            context=context,
            request=request,
        )
        my_form.form = my_deform_form
        res = my_form.submitted()
        assert res is True

    def test_submitted_true_button(self):
        """
        Test submitted true button
        """
        post_dict = {
            "foo": "bar",
            "submit": True,
            "__formid__": "my_form_id"
        }
        request = DummyRequest(post=post_dict)
        context = DummyResource()

        my_deform_form = DeformFormMockValidating()

        my_form = FormControllerMock(
            context=context,
            request=request,
        )
        my_form.form = my_deform_form
        my_form.formid = "deform"
        res = my_form.submitted(button='submit')
        assert res is True

    def test_redirect_str(self):
        """
        Test redirect str
        """
        request = DummyRequest()
        request.session['forms'] = {'FormControllerMock': 'form'}
        context = DummyResource(path="/foo")

        my_form = FormControllerMock(
            context=context,
            request=request,
        )
        my_form.redirect(resource="/foo")
        assert isinstance(my_form.response, HTTPFound)
        # assert form has been removed from session
        assert request.session['forms'] == {}

    def test_redirect_ressource_instance(self):
        """
        Test redirect resource instance
        """
        request = DummyRequest()
        request.session['forms'] = {
            'FormControllerMock': 'form'}
        context = DummyResource()
        my_form = FormControllerMock(
            context=context,
            request=request,
        )
        mock_resource = ResourceBase(request)
        my_form.redirect(mock_resource)
        assert isinstance(my_form.response, HTTPFound)
        # assert form has been removed from session
        assert request.session['forms'] == {}

    def test_redirect_ressource_class(self):
        """
        Test redirect resource class
        """
        request = DummyRequest()
        request.session['forms'] = {
            'FormControllerMock': 'form'}
        context = DummyResource()
        my_form = FormControllerMock(
            context=context,
            request=request,
        )
        mock_resource = ResourceBase
        my_form.redirect(mock_resource)
        assert isinstance(my_form.response, HTTPFound)
        # assert form has been removed from session
        assert request.session['forms'] == {}

    def test_clean(self):
        """
        Test clean
        """
        request = DummyRequest()
        request.session['forms'] = {
            'FormControllerMock': 'form'}
        context = DummyResource()
        my_form = FormControllerMock(
            context=context,
            request=request,
        )
        my_form.clean()
        assert my_form._form is None
        assert my_form._data == {}
        assert my_form.validationfailure is None
