# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

from ..base import FunctionalTestBase


class TestLogin(FunctionalTestBase):

    def setUp(self):
        self.session()

    def test_required_field_email(self):
        '''
        Is field email required?
        '''

        res1 = self.url('login', status=200)
        form = res1.form
        res2 = form.submit('WebUsersubmit')
        self.assertIn(
            '<p class="help-block" id="error-email">Required</p>',
            res2.body
        )

    def test_required_field_password(self):
        '''
        Is field password required?
        '''

        res1 = self.url('login', status=200)
        form = res1.form
        res2 = form.submit('WebUsersubmit')
        self.assertIn(
            '<p class="help-block" id="error-password">Required</p>',
            res2.body
        )

    def test_email_validator(self):
        '''
        Is email checked for validity?
        '''

        res1 = self.url('login', status=200)
        form = res1.form
        form['email'] = 'notanemail'
        res2 = form.submit('WebUsersubmit')
        self.assertIn(
            '<p class="help-block" id="error-email">Invalid email address</p>',
            res2.body
        )

    def test_login_with_wrong_email(self):
        '''
        Does login with unregistered email fail?
        '''

        res1 = self.url('login', status=200)
        form = res1.form
        form['email'] = 'wrong@username.test'
        form['password'] = 'wrongpassword'
        res2 = form.submit('WebUsersubmit')
        self.assertIn('<p class="errorMsg">Login failed</p>', res2.body)

    def test_login_with_wrong_password(self):
        '''
        Does login with wrong password fail?
        '''

        res1 = self.url('login', status=200)
        form = res1.form
        form['email'] = 'meik@c3s.cc'
        form['password'] = 'wrongpassword'
        res2 = form.submit('WebUsersubmit')
        self.assertIn('<p class="errorMsg">Login failed</p>', res2.body)

    def test_login_with_right_credentials(self):
        '''
        Does login with right credentials succeed?
        '''

        res1 = self.url('login', status=200)
        form = res1.form
        form['email'] = 'meik@c3s.cc'
        form['password'] = 'meik'
        res2 = form.submit('WebUsersubmit')
        self.assertIn('The resource was found at', res2.body)
        res3 = res2.follow()
        self.assertIn(
            '<div class="cs-content cs-backend container">', res3.body
        )