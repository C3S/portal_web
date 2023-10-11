# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

import pytest


@pytest.fixture(autouse=True, scope='class')
def web_user(create_web_user):
    create_web_user(
        email='verified@username.test',
        password='rightpassword',
        opt_in_state='opted-in',
    )
    create_web_user(
        email='unverified@username.test',
        password='rightpassword',
    )


@pytest.mark.usefixtures('reset')
class TestLogin:
    """
    App login test class
    """
    def test_required_field_email(self, gui):
        """
        Is field email required?
        """
        res1 = gui.get('/', status=200)
        form = res1.forms['LoginWebuser']
        res2 = form.submit('LoginWebusersubmit')
        assert (
            '<p class="help-block" id="error-login-email">Required</p>'
        ) in str(res2.body)

    def test_required_field_password(self, gui):
        """
        Is field password required?
        """
        res1 = gui.get('/', status=200)
        form = res1.forms['LoginWebuser']
        res2 = form.submit('LoginWebusersubmit')
        assert (
            '<p class="help-block" id="error-login-password">Required</p>'
        ) in str(res2.body)

    def test_email_validator(self, gui):
        """
        Is email checked for validity?
        """
        res1 = gui.get('/', status=200)
        form = res1.forms['LoginWebuser']
        form['email'] = 'notanemail'
        res2 = form.submit('LoginWebusersubmit')
        assert (
            '<p class="help-block" id="error-login-email">'
            'Invalid email address</p>'
        ) in str(res2.body)

    def test_unverified_login_with_wrong_password(self, gui):
        """
        Does login with unverified account and wrong password fail?
        """
        res1 = gui.get('/', status=200)
        form = res1.forms['LoginWebuser']
        form['email'] = 'unverified@username.test'
        form['password'] = 'wrongpassword'
        res2 = form.submit('LoginWebusersubmit')
        assert (
            '<p class="errorMsg">User mail address not verified yet</p>'
        ) in str(res2.body)

    def test_unverified_login_with_right_password(self, gui):
        """
        Does login with unverified account and right password fail?
        """
        res1 = gui.get('/', status=200)
        form = res1.forms['LoginWebuser']
        form['email'] = 'unverified@username.test'
        form['password'] = 'rightpassword'
        res2 = form.submit('LoginWebusersubmit')
        assert (
            '<p class="errorMsg">User mail address not verified yet</p>'
        ) in str(res2.body)

    def test_login_with_wrong_email(self, gui):
        """
        Does login with unregistered email fail?
        """
        res1 = gui.get('/', status=200)
        form = res1.forms['LoginWebuser']
        form['email'] = 'wrong@username.test'
        form['password'] = 'rightpassword'
        res2 = form.submit('LoginWebusersubmit')
        assert '<p class="errorMsg">Login failed</p>' in str(res2.body)

    def test_login_with_wrong_password(self, gui):
        """
        Does login with wrong password fail?
        """
        res1 = gui.get('/', status=200)
        form = res1.forms['LoginWebuser']
        form['email'] = 'verified@username.test'
        form['password'] = 'wrongpassword'
        res2 = form.submit('LoginWebusersubmit')
        assert '<p class="errorMsg">Login failed</p>' in str(res2.body)

    def test_login_with_right_credentials(self, gui):
        """
        Does login with right credentials succeed?
        """
        res1 = gui.get('/', status=200)
        form = res1.forms['LoginWebuser']
        form['email'] = 'verified@username.test'
        form['password'] = 'rightpassword'
        res2 = form.submit('LoginWebusersubmit')
        assert '<p class="errorMsg">Login failed</p>' not in str(res2.body)
        res3 = res2.maybe_follow()
        assert '<div class="cs-content cs-backend' in str(res3.body)
