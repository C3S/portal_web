# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

import colander
import deform
import logging

from . import FormController
from ...models import (
    Tdb,
    WebUser
)
from ...services import (
    _,
    send_mail
)

log = logging.getLogger(__name__)


# --- Controller --------------------------------------------------------------

class RegisterWebuser(FormController):
    """
    form controller for web_user login
    """

    def controller(self):
        self.form = register_form()
        self.render()
        if self.submitted() and self.validate():
            self.register()
        return self.response

    # --- Stages --------------------------------------------------------------

    # --- Conditions ----------------------------------------------------------

    # --- Actions -------------------------------------------------------------

    @Tdb.transaction(readonly=False)
    def register(self):
        _web_user = {
            'email': self.appstruct['email'],
            'password': self.appstruct['password']
        }
        web_users = WebUser.create([_web_user])

        # check, if web user creation was successful
        if not web_users:
            log.info("web_user creation not successful.")
            return False
        web_user = web_users[0]
        log.info("web_user creation successful: %s" % web_user.email)

        # user feedback
        self.request.session.flash(
            _(
                u"Registration was successful. You should recieve an email "
                u"with further instructions, how to verify your email address."
            ),
            'main-alert-success'
        )

        # send email
        send_mail(
            self.request,
            subject=_(u"Verification Mail"),
            sender="test@portal.test",
            recipients=[self.appstruct['email']],
            body=_(u"Thanks for your registration. Please visit this link to "
                   u"verify your email address") + ": %s" % (
                     self.request.resource_url(
                         self.request.root, 'verify_email',
                         WebUser.get_opt_in_uuid_by_id(web_user.id)
                     )
                 )
        )

        # reset form
        self.remove()
        self.render()


# --- Validators --------------------------------------------------------------

def email_is_unique(value):
    if not WebUser.search_by_email(value):
        return True
    return _(u'Email already registered')


# --- Options -----------------------------------------------------------------

# --- Fields ------------------------------------------------------------------

class EmailField(colander.SchemaNode):
    oid = "register-email"
    schema_type = colander.String
    validator = colander.All(
        colander.Email(),
        colander.Function(email_is_unique)
    )


class CheckedPasswordField(colander.SchemaNode):
    oid = "register-password"
    schema_type = colander.String
    validator = colander.Length(min=8)
    widget = deform.widget.CheckedPasswordWidget()


# --- Schemas -----------------------------------------------------------------

class RegisterSchema(colander.MappingSchema):
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
