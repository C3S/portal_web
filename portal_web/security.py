from pyramid.authentication import AuthTktCookieHelper
from pyramid.authorization import ACLHelper, Authenticated, Everyone

from .models import WebUser


class SecurityPolicy:
    def __init__(self, secret):
        self.helper = AuthTktCookieHelper(secret, hashalg='sha512')

    def identity(self, request):
        identity = self.helper.identify(request)
        if identity is None:
            return None

        userid = identity['userid']
        principals = WebUser.groupfinder(userid, request)
        if principals is not None:
            return {
                'userid': userid,
                'principals': principals,
            }

    def authenticated_userid(self, request):
        identity = request.identity
        if identity is not None:
            return identity['userid']

    def permits(self, request, context, permission):
        identity = request.identity
        principals = set([Everyone])

        if identity is not None:
            principals.add(Authenticated)
            principals.add(identity['userid'])
            principals.update(identity['principals'])

        return ACLHelper().permits(context, principals, permission)

    def remember(self, request, userid, **kw):
        return self.helper.remember(request, userid, **kw)

    def forget(self, request, **kw):
        return self.helper.forget(request, **kw)
