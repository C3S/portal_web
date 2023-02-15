# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

from ..base import FunctionalTestBase
from ..testdata import TestDataPortal


class TestLogin(FunctionalTestBase, TestDataPortal):

    @classmethod
    def setUpClass(cls):
        """
        Creates test data.
        """
        super(TestLogin, cls).setUpClass()
        cls.createWebUser(
            email='right@username.test',
            password='rightpassword'
        )

    def setUp(self):
        """
        Renews the session for each test.
        """
        self.session()

    def test_required_field_email(self):
        """
        Is field email required?
        """

        res1 = self.url('gui', '/', status=200)
        form = res1.forms['LoginWebuser']
        res2 = form.submit('LoginWebusersubmit')
        self.assertIn(
            '<p class="help-block" id="error-login-email">Required</p>',
            str(res2.body)
        )

    def test_required_field_password(self):
        """
        Is field password required?
        """
        res1 = self.url('gui', '/', status=200)
        form = res1.forms['LoginWebuser']
        res2 = form.submit('LoginWebusersubmit')
        self.assertIn(
            '<p class="help-block" id="error-login-password">Required</p>',
            str(res2.body)
        )

    def test_email_validator(self):
        """
        Is email checked for validity?
        """
        res1 = self.url('gui', '/', status=200)
        form = res1.forms['LoginWebuser']
        form['email'] = 'notanemail'
        res2 = form.submit('LoginWebusersubmit')
        self.assertIn(
            '<p class="help-block" id="error-login-email">'
            + 'Invalid email address</p>',
            str(res2.body)
        )

    def test_login_with_wrong_email(self):
        """
        Does login with unregistered email fail?
        """
        res1 = self.url('gui', '/', status=200)
        form = res1.forms['LoginWebuser']
        form['email'] = 'wrong@username.test'
        form['password'] = 'wrongpassword'
        res2 = form.submit('LoginWebusersubmit')
        self.assertIn('<p class="errorMsg">Login failed</p>', str(res2.body))

    def test_login_with_wrong_password(self):
        """
        Does login with wrong password fail?
        """
        res1 = self.url('gui', '/', status=200)
        form = res1.forms['LoginWebuser']
        form['email'] = 'right@username.test'
        form['password'] = 'wrongpassword'
        res2 = form.submit('LoginWebusersubmit')
        res3 = res2.maybe_follow()
        self.assertIn('<p class="errorMsg">Login failed</p>', str(res3.body))

    def test_login_with_right_credentials(self):
        """
        Does login with right credentials succeed?
        """
        res1 = self.url('gui', '/', status=200)
        form = res1.forms['LoginWebuser']
        form['email'] = 'right@username.test'
        form['password'] = 'rightpassword'
        res2 = form.submit('LoginWebusersubmit')
        self.assertNotIn(
            '<p class="errorMsg">Login failed</p>',
            str(res2.body)
        )
        res3 = res2.maybe_follow()
        self.assertIn('<div class="cs-content cs-backend', str(res3.body))
