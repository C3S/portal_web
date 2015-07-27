# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import colander
import deform
import logging

from . import LoginWebuser
from ...models import WebUser
from ...services import _

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class RegisterWebuser(LoginWebuser):
    """
    form controller for web_user login
    """

    def controller(self):

        self.form = register_form()

        if self.submitted() and self.validate():
            self.register()
            self.login()

        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    def register(self):
        web_user = {
            'email': self.appstruct['email'],
            'password': self.appstruct['password']
        }
        WebUser.create([web_user])
        log.info("web_user creation successful: %s" % self.appstruct['email'])


# --- Validators --------------------------------------------------------------

def email_is_unique(value):
    if not WebUser.search_by_email(value):
        return True
    return _(u'Email already registered')


# --- Options -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

class EmailField(colander.SchemaNode):
    oid = "email"
    schema_type = colander.String
    validator = colander.All(
        colander.Email(),
        colander.Function(email_is_unique)
    )


class CheckedPasswordField(colander.SchemaNode):
    oid = "password"
    schema_type = colander.String
    validator = colander.Length(min=8)
    widget = deform.widget.CheckedPasswordWidget()


# --- Schemas -----------------------------------------------------------------

class RegisterSchema(colander.MappingSchema):
    title = _(u"Register")
    email = EmailField(
        title=_(u"Email")
    )
    password = CheckedPasswordField(
        title=_(u"Password")
    )


# --- Forms -------------------------------------------------------------------

def register_form():
    return deform.Form(
        schema=RegisterSchema(),
        buttons=[
            deform.Button('submit', _(u"Submit"))
        ]
    )
