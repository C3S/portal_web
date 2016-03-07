# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import logging

from pyramid.renderers import render
from pyramid.response import Response
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import (
    view_config,
    view_defaults
)

from . import ViewBase
from .forms import (
    LoginWebuser,
    RegisterWebuser,
)

from ..models import WebUser

log = logging.getLogger(__name__)


@view_defaults(
    context='..resources.FrontendResource',
    permission=NO_PERMISSION_REQUIRED)
class PagePortalViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/page/home.pt')
    def home(self):
        self.register_form(LoginWebuser)
        self.register_form(RegisterWebuser)
        return self.process_forms()

    @view_config(
        name='help',
        renderer='../templates/page/page.pt')
    def help(self):
        page = render('../templates/page/help.pt', {}, request=self.request)
        return {'page': page}

    @view_config(
        name='privacy',
        renderer='../templates/page/page.pt')
    @view_config(
        name='privacy',
        context='..resources.BackendResource',
        renderer='../templates/web_user/page.pt')
    def privacy(self):
        page = render('../templates/page/privacy.pt', {}, request=self.request)
        return {'page': page}

    @view_config(
        name='imprint',
        renderer='../templates/page/page.pt')
    @view_config(
        name='imprint',
        context='..resources.BackendResource',
        renderer='../templates/web_user/page.pt')
    def imprint(self):
        page = render('../templates/page/imprint.pt', {}, request=self.request)
        return {'page': page}

    @view_config(
        name='faq',
        context='..resources.BackendResource',
        renderer='../templates/web_user/page.pt')
    def faq(self):
        page = render('../templates/page/faq.pt', {}, request=self.request)
        return {'page': page}

    @view_config(
        name='register',
        renderer='../templates/page/register.pt')
    def register(self):
        self.register_form(RegisterWebuser)
        return self.process_forms()

    @view_config(
        name='login',
        renderer='../templates/page/login.pt')
    def login(self):
        self.register_form(LoginWebuser)
        return self.process_forms()

    @view_config(
        name='verify_email',
        renderer='../templates/page/page.pt')
    def verify_email(self):
        uuid = self.request.subpath[-1]
        if uuid:
            if WebUser.search_by_uuid(str(uuid)):
                if WebUser.update_opt_in_state_by_uuid(str(uuid), 'opted-in'):
                    page = render('../templates/page/verify_email.pt',
                           {'yesno':'', 'error':''},
                           request=self.request)
                else:
                    page = render('../templates/page/verify_email.pt',
                           {'yesno':'not ', 'error':'Update not successful'},
                           request=self.request)
            else:
                page = render('../templates/page/verify_email.pt',
                       {'yesno':'not ', 'error':'Wrong validation code in URL'},
                       request=self.request)
        else:
            page = render('../templates/page/verify_email.pt',
                   {'yesno':'not ', 'error':'Missing validation code in URL'},
                   request=self.request)

        return {'page': page}
