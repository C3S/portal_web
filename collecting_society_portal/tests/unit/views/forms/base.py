
from pyramid.testing import (
    DummyRequest,
    DummyResource
    )

from ....base import UnitTestBase

# from ....views.forms.base import FormController
from collecting_society_portal.views.forms.base import (
    FormController,
    # TmpFile
)


class FormControllerMock(FormController):

    def controller(self):
        pass


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


class TestFormBase(UnitTestBase):

    def setUp(self):
        pass

    def test_formcontroller_controller(self):
        """
        Test the FormController class
        """
        my_form = FormControllerMock()

        my_form

    def test_formcontroller_getstate(self):
        """
        Test the FormController class
        """
        my_form = FormControllerMock()

        res = my_form.__getstate__()
        # res = {
        #     '_name': 'FormControllerMock',
        #     'persistent': False,
        #     'appstruct': {},
        #     '_data': {},
        #     '__stage__': None,
        #     'stage': None}
        self.assertEqual(res['_name'], 'FormControllerMock')
        self.assertEqual(res['persistent'], False)

    def test_formcontroller_setstate(self):
        """
        Test the FormController class
        """
        my_form = FormControllerMock()

        res = my_form.__getstate__()
        # res = {
        #     '_name': 'FormControllerMock',
        #     'persistent': False,
        #     'appstruct': {},
        #     '_data': {},
        #     '__stage__': None,
        #     'stage': None}
        self.assertEqual(res['_name'], 'FormControllerMock')
        self.assertEqual(res['persistent'], False)

        new_state = {
            '_name': 'FormControllerMoo',
            'persistent': True,
            'appstruct': {"foo": "moo"},
            '_data': {},
            '__stage__': None,
            'stage': None}
        my_form.__setstate__(new_state)
        res = my_form.__getstate__()
        self.assertEqual(res['_name'], 'FormControllerMoo')
        self.assertEqual(res['persistent'], True)
        # self.assertEqual(res['appstruct'], dict("foo: "moo"))

    def test_validate(self):
        """
        Test validation success
        """
        post_dict = {"foo": "bar"}
        self.request = DummyRequest(post=post_dict)
        self.context = DummyResource()

        my_deform_form = DeformFormMockValidating()

        my_form = FormControllerMock(
            context=self.context,
            request=self.request,

        )
        my_form.form = my_deform_form
        res = my_form.validate()
        self.assertTrue(res)
        vres = my_form.valid()
        vres
        self.assertTrue(vres)

    def test_validate_not(self):
        """
        Test validation failure
        """
        post_dict = {"foo": "bar"}
        self.request = DummyRequest(post=post_dict)
        self.context = DummyResource()

        my_deform_form = DeformFormMockNonValidating()

        my_form = FormControllerMock(
            context=self.context,
            request=self.request,

        )
        my_form.form = my_deform_form
        res = my_form.validate()
        self.assertFalse(res)
        self.assertIn(my_form.validationfailure.error, 'my error')

    def test_render(self):
        """
        Test render
        """
        post_dict = {"foo": "bar"}
        self.request = DummyRequest(post=post_dict)
        self.context = DummyResource()

        my_deform_form = DeformFormMockValidating()

        my_form = FormControllerMock(
            context=self.context,
            request=self.request,

        )
        my_form.form = my_deform_form
        res = my_form.render()
        res
        self.assertIn('FormControllerMock', my_form.response)
        self.assertIn(my_form.response['FormControllerMock'], '<form></form>')

    def test_process(self):
        """
        Test process forms
        """
        self.request = DummyRequest()
        self.context = DummyResource()

        my_deform_form = DeformFormMockValidating()

        my_form = FormControllerMock(
            context=self.context,
            request=self.request,

        )
        my_form.form = my_deform_form
        res = my_form.process(self.context, self.request)
        res  # should be the controller

    def test_data(self):
        """
        Test data
        """
        post_dict = {"foo": "bar"}
        self.request = DummyRequest(post=post_dict)
        self.context = DummyResource()

        my_deform_form = DeformFormMockValidating()

        my_form = FormControllerMock(
            context=self.context,
            request=self.request,

        )
        my_form.form = my_deform_form
        res = my_form.data
        self.assertEqual(res, {})

    def test_submitted_false(self):
        """
        Test submitted false
        """
        post_dict = {"foo": "bar"}
        self.request = DummyRequest(post=post_dict)
        self.context = DummyResource()

        my_deform_form = DeformFormMockValidating()

        my_form = FormControllerMock(
            context=self.context,
            request=self.request,

        )
        my_form.form = my_deform_form
        res = my_form.submitted()
        self.assertEqual(res, False)

    def test_submitted_false_nodata(self):
        """
        Test submitted false nodata
        """
        post_dict = {}
        self.request = DummyRequest(post=post_dict)
        self.context = DummyResource()

        my_deform_form = DeformFormMockValidating()

        my_form = FormControllerMock(
            context=self.context,
            request=self.request,

        )
        my_form.form = my_deform_form
        res = my_form.submitted()
        self.assertEqual(res, False)

    def test_submitted_true(self):
        """
        Test submitted true
        """
        post_dict = {
            "foo": "bar",
            "__formid__": "my_form_id"
        }
        self.request = DummyRequest(post=post_dict)
        self.context = DummyResource()

        my_deform_form = DeformFormMockValidating()

        my_form = FormControllerMock(
            context=self.context,
            request=self.request,

        )
        my_form.form = my_deform_form
        res = my_form.submitted()
        self.assertEqual(res, True)

    def test_submitted_true_button(self):
        """
        Test submitted true button
        """
        post_dict = {
            "foo": "bar",
            "submit": True,
            "__formid__": "my_form_id"
        }
        self.request = DummyRequest(post=post_dict)
        self.context = DummyResource()

        my_deform_form = DeformFormMockValidating()

        my_form = FormControllerMock(
            context=self.context,
            request=self.request,

        )
        my_form.form = my_deform_form
        my_form.formid = "deform"
        res = my_form.submitted(button='submit')
        res
        self.assertEqual(res, True)

    def test_redirect_str(self):
        """
        Test redirect str
        """
        self.request = DummyRequest()
        self.request.session['forms'] = {
            'FormControllerMock': 'form'}
        self.context = DummyResource(path="/foo")

        self.assertIn(
            self.request.session['forms']['FormControllerMock'],
            'form')

        # my_deform_form = DeformFormMockValidating()

        my_form = FormControllerMock(
            context=self.context,
            request=self.request,

        )
        my_form.redirect(resource="/foo")
        # assert form has been removed from session
        self.assertEqual(
            self.request.session['forms'], {})

    def test_redirect_res(self):
        """
        Test redirect resource
        """
        self.request = DummyRequest()
        self.request.session['forms'] = {
            'FormControllerMock': 'form'}
        self.context = DummyResource()

        # my_deform_form = DeformFormMockValidating()

        my_form = FormControllerMock(
            context=self.context,
            request=self.request,

        )
        my_form.redirect(DummyResource)

    def test_clean(self):
        """
        Test clean
        """
        self.request = DummyRequest()
        self.request.session['forms'] = {
            'FormControllerMock': 'form'}
        self.context = DummyResource()

        # my_deform_form = DeformFormMockValidating()

        my_form = FormControllerMock(
            context=self.context,
            request=self.request,

        )
        my_form.clean()
        self.assertTrue(my_form._form is None)
        self.assertEqual(my_form._data, {})
        self.assertIsNone(my_form.validationfailure)


# class TestTmpFile(UnitTestBase):
#
#    def test_tmpfile(self):
#
#        tf = TmpFile()
