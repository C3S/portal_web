# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import logging

from pyramid.security import forget
from pyramid.httpexceptions import HTTPFound
from pyramid.view import (
    view_config,
    view_defaults
)

from . import ViewBase
from ..resources import FrontendResource

log = logging.getLogger(__name__)


@view_defaults(context='..resources.BackendResource')
class WebUserViews(ViewBase):

    @view_config(
        name='',
        renderer='../templates/web_user/dashboard.pt',
        permission='read'
    )
    def dashboard(self):
        return {}

    @view_config(
        context='..resources.NewsResource',
        name='',
        renderer='../templates/web_user/news.pt',
        permission='authenticated'
    )
    def news(self):
        log.debug(self.context.registry['content']['news'])
        return {}

    @view_config(
        context='..resources.ArticleResource',
        name='',
        renderer='../templates/web_user/article.pt',
        permission='authenticated'
    )
    def article(self):
        return {}

    @view_config(
        name='logout',
        permission='authenticated'
    )
    def logout(self):
        self.request.session.invalidate()
        log.info(
            "web_user logout successful: %s" %
            self.request.unauthenticated_userid
        )
        headers = forget(self.request)
        return HTTPFound(
            self.request.resource_path(FrontendResource(self.request)),
            headers=headers
        )
