# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import logging
from copy import deepcopy

from collections import (
    Mapping,
    defaultdict,
    OrderedDict
)

from pyramid.security import (
    Allow,
    Authenticated,
    Everyone,
    ALL_PERMISSIONS
)

from .services import _
from .models import (
    WebUser
)
from .views.widgets import news_widget

log = logging.getLogger(__name__)


def include_web_resources(config):
    BackendResource.add_child(NewsResource)
    BackendResource.add_child(DebugResource)


class ResourceBase(object):
    __name__ = None
    __parent__ = None
    __children__ = {}
    __registry__ = {
        'content': {},
        'static': {},
        'menues': {},
        'widgets': {}
    }
    __acl__ = []

    _parentclass = None

    def __init__(self, request):
        if self.__parent__:
            instance = self.__parent__(request)
            self.__parent__ = instance
        self.request = request
        self.data = None

    def __getitem__(self, key):
        if key in self.__children__:
            return self.__children__[key](self.request)
        raise KeyError(key)

    def __str__(self):
        name = 'None'
        if hasattr(self.__parent__, '__name__'):
            name = self.__parent__.__name__
        return (
            "context: %s.%s\n"
            "context.__parent__: %s\n"
            "context.__children__: %s\n"
            "context.data: %s\n"
            "context.registry:\n%s"
        ) % (
            self.__class__.__module__, self.__class__.__name__,
            name,
            self.__children__,
            self.data,
            self.registry,
        )

    @classmethod
    def add_child(cls, val):
        val.__parent__ = cls
        cls.__children__[val.__dict__['__name__']] = val

    @classmethod
    def merge_registry(cls, orig_dict, new_dict):
        """
        Recursively merge dict-like objects.
        If a value in new_dict is {}, the key is removed in orig_dict
        """
        for key, val in new_dict.iteritems():
            # delete key if val == {}
            if isinstance(val, Mapping) and not val:
                orig_dict.pop(key, None)
            # update with OrderedDict
            if isinstance(val, OrderedDict):
                r = cls.merge_registry(
                    OrderedDict(orig_dict.get(key, {})),
                    val
                )
                orig_dict[key] = r
            # update with Mapping
            elif isinstance(val, Mapping):
                r = cls.merge_registry(orig_dict.get(key, {}), val)
                orig_dict[key] = r
            # update with other objects
            elif isinstance(orig_dict, Mapping):
                orig_dict[key] = new_dict[key]
            else:
                orig_dict = {key: new_dict[key]}
        return orig_dict

    @classmethod
    def extend_registry(cls, func):
        _orig_reg = cls.__registry__

        def _registry_extension(self):
            orig_dict = _orig_reg
            if isinstance(orig_dict, property):
                orig_dict = orig_dict.fget(self)
            return cls.merge_registry(dict(orig_dict), func(self))
        cls.__registry__ = property(_registry_extension)

    @property
    def registry(self):
        if not hasattr(self, '_registry_cache'):
            orig_dict = ResourceBase.__registry__
            if self.__parent__:
                orig_dict = self.__parent__.registry
            if isinstance(orig_dict, property):
                orig_dict = orig_dict.fget(self)
            self._registry_cache = self.merge_registry(
                deepcopy(orig_dict), self.__registry__
            )
        return self._registry_cache

    def dict(self):
        return defaultdict(self.dict)


class WebRootFactory(object):
    def __new__(cls, request):
        if request.user:
            return BackendResource(request)
        return FrontendResource(request)


class ApiRootFactory(ResourceBase):
    __name__ = ""
    __parent__ = None
    __children__ = {}

    @property
    def __acl__(self):
        return [
            (Allow, Everyone, 'authenticated'),
            (Allow, 'group:administrator', ALL_PERMISSIONS)
        ]


class FrontendResource(ResourceBase):
    __name__ = ""
    __parent__ = None
    __children__ = {}

    @property
    def __registry__(self):
        reg = self.dict()
        # logo
        reg['static']['logo'] = self.request.static_path(
            'collecting_society_portal:static/img/logo.png'
        )
        # menue page
        reg['menues']['page'] = [
            {
                'name': _(u'overview'),
                'page': 'overview'
            },
            {
                'name': _(u'details'),
                'page': 'details'
            },
            {
                'name': _(u'about c3s'),
                'page': 'aboutc3s'
            },
            {
                'name': _(u'contact'),
                'page': 'contact'
            },
            {
                'name': _(u'imprint'),
                'page': 'imprint'
            }
        ]
        return reg


class BackendResource(ResourceBase):
    __name__ = ""
    __parent__ = None
    __children__ = {}

    @property
    def __registry__(self):
        reg = self.dict()
        # logo
        reg['static']['logo'] = self.request.static_path(
            'collecting_society_portal:static/img/logo.png'
        )
        # menue portal
        reg['menues']['portal'] = [
            {
                'name': _(u'Profile'),
                'url': None
            },
            {
                'name': _(u'News'),
                'url': self.request.resource_path(
                    BackendResource(self.request), 'news'
                )
            },
            {
                'name': _(u'FAQ'),
                'url': self.request.resource_path(
                    BackendResource(self.request), 'faq'
                )
            },
            {
                'name': _(u'Privacy'),
                'url': self.request.resource_path(
                    BackendResource(self.request), 'privacy'
                )
            },
            {
                'name': _(u'Imprint'),
                'url': self.request.resource_path(
                    BackendResource(self.request), 'imprint'
                )
            },
            {
                'name': _(u'Logout'),
                'url': self.request.resource_path(
                    BackendResource(self.request), 'logout'
                )
            }
        ]
        # news
        reg['content']['news'] = OrderedDict()
        reg['content']['news']['1'] = {
            'header': _(u'News Article 1'),
            'template': '../content/news/news1'
        }
        reg['content']['news']['2'] = {
            'header': _(u'News Article 2'),
            'template': '../content/news/news2'
        }
        reg['content']['news']['3'] = {
            'header': _(u'News Article 3'),
            'template': '../content/news/news3'
        }
        # widgets content-right
        reg['widgets']['content-right'] = [
            news_widget
        ]
        return reg

    @property
    def __acl__(self):
        return [
            (Allow, self.request.unauthenticated_userid, 'read'),
            (Allow, Authenticated, 'authenticated'),
            (Allow, 'group:administrator', ALL_PERMISSIONS)
        ]

    def __init__(self, request):
        super(BackendResource, self).__init__(request)
        self.web_user = WebUser.current_web_user(self.request)


class NewsResource(ResourceBase):
    __name__ = "news"
    __parent__ = BackendResource
    __children__ = {}
    __registry__ = {}
    __acl__ = [
        (Allow, Authenticated, 'authenticated')
    ]

    def __getitem__(self, key):
        if key in self.registry['content']['news']:
            article = ArticleResource(self.request, key)
            self.__children__[key] = article
            article.__name__ = key
            return article
        raise KeyError(key)


class ArticleResource(ResourceBase):
    __name__ = "article"
    __parent__ = NewsResource
    __children__ = {}
    __registry__ = {}
    __acl__ = [
        (Allow, Authenticated, 'authenticated')
    ]

    def __init__(self, request, id):
        super(ArticleResource, self).__init__(request)
        self.article = self.registry['content']['news'][id]


class DebugResource(ResourceBase):
    __name__ = "debug"
    __parent__ = BackendResource
    __registry__ = {}
    __acl__ = [
        (Allow, Authenticated, 'authenticated')
    ]
