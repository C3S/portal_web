
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

    formid = 'deform'

    def validate(self, data):
        return {'foo': 'bar'}

    def render(self):
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
        test the FormController class
        """
        my_form = FormControllerMock()

        my_form

    def test_validate(self):
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

    def test_validate_not(self):
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

    # def test_render(self):
    #     post_dict = {"foo": "bar"}
    #     self.request = DummyRequest(post=post_dict)
    #     self.context = DummyResource()

    #     my_deform_form = DeformFormMockValidating()

    #     my_form = FormControllerMock(
    #         context=self.context,
    #         request=self.request,

    #     )
    #     my_form.form = my_deform_form
    #     appstruct = {"foo": "bar"}
    #     #res = my_form.render(appstruct=appstruct)
    #     res = my_form.render(appstruct)
    #     self.assertFalse(res)

    def test_data(self):
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


# class TestTmpFile(UnitTestBase):
#
#    def test_tmpfile(self):
#
#        tf = TmpFile()
