# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

from pyramid.security import remember
import colander
import deform
import logging

from . import FormController
from ...services import _
from ...models import WebUser
from ...resources import BackendResource

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class LoginWebuser(FormController):
    """
    form controller for web_user login
    """

    def controller(self):
        self.form = login_form()
        self.render()
        if self.submitted() and self.validate():
            self.login()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    def login(self):
        self.redirect(
            BackendResource, '',
            headers=remember(self.request, self.appstruct['email'])
        )
        log.info("web_user login successful: %s" % self.appstruct['email'])


# --- Validators --------------------------------------------------------------

def authentication_is_successful(values):
    if not WebUser.search_by_email(values['email']):
        return _(u'Login failed')
    if not (WebUser.get_opt_in_state_by_email(values['email']) == 'opted-in'):
        return _(u'User mail address not verified yet')
    if WebUser.authenticate(values['email'], values['password']):
        return True
    log.info("web_user login failed: %s" % values['email'])
    return _(u'Login failed')


# --- Options -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

class EmailField(colander.SchemaNode):
    oid = "login-email"
    schema_type = colander.String
    validator = colander.Email()


class PasswordField(colander.SchemaNode):
    oid = "login-password"
    schema_type = colander.String
    widget = deform.widget.PasswordWidget()


# --- Schemas -----------------------------------------------------------------

class LoginSchema(colander.MappingSchema):
    email = EmailField(
        title=_(u"Email")
    )
    password = PasswordField(
        title=_(u"Password")
    )


# --- Forms -------------------------------------------------------------------

def login_form():
    return deform.Form(
        schema=LoginSchema(
            validator=colander.Function(authentication_is_successful)
        ),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
