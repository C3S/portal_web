# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import colander
import deform
import logging

from . import LoginWebuser
from ...models import WebUser
from ...services import _
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

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

        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    def register(self):

        web_user = {
            'email': self.appstruct['email'],
            'password': self.appstruct['password']
        }
        new_web_user = WebUser.create([web_user])

        # check, if web user creation was successful
        if WebUser.search_by_id(new_web_user[0]['id']):
            log.info("web_user creation successful: %s" % web_user['email'])

            mailer = get_mailer(self.request)
            message = Message(subject="VerificationMail",
                              sender="test@adore-music.com",
                              recipients=[self.appstruct['email']],
                              body="Thanks for your registration. Please visit"
                                   " this link for verification: "
                                   "https://www.adore-music.com/verify_email/"
                                   "%s" % WebUser.get_opt_in_uuid_by_id(
                                       new_web_user[0]['id'])
                              )

            # mailer.send_immediately(message, fail_silently=False)
            log.debug(dir(message))
            log.debug(message.body)
        else:
            log.info("web_user creation not successful.")

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
