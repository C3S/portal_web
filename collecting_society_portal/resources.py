# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

"""
Base resources including base, web-/apirootfactory, back-/frontend, debug
"""

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
)


log = logging.getLogger(__name__)


class ResourceBase(object):
    """
    Base class for `traversal`_ based resources providing a content registry.

    Resources are used to form flexible, hierarchical parent-child structures
    to reflect the url. In the first step of traversal, the URL is mapped to a
    resource and in the second step the resource is mapped to a pyramid view.

    Children may be added to resources via the `add_child()` function.

    The content registry may be used to assign different types of content to a
    resource, which is provided to pyramid views and the template engine as
    `context`. Different types might be:

    - meta (e.g. browser title, keywords, desciption, etc.)
    - content (e.g. page content, news articles, etc.)
    - static (e.g. css files, logo images, etc.)
    - menues (e.g. top navigation, sidebar navigation, etc.)
    - widgets (dynamic content elements used in different locations)

    The registry of a parent class is inherited to and may be extended by its
    children. This allows for content elements to be present on a
    whole branch of resources, like logos or menues.

    The registry may be extended by the `extend_registry` decorator function.

    Note:
        In later versions the content of the registry might be stored in and
        retrieved from a database to provide CMS features.

    Args:
        request (pyramid.request.Request): Current request.

    Classattributes:
        __name__ (str): URL path segment.
        __parent__ (obj): Instance of parent resource.
        __children__ (dict): Children resources.
        __registry__ (dict): Content registry
            (dictionary or property function returning a dictionary).
        __acl__ (list): Access control list
            (list of tupels or property function returning a list of tupels).

    Attributes:
        _registry_cache (dict): Cached content registry.
        request (pyramid.request.Request): Current request.

    .. _traversal:
       http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/traversal.html
    """
    __name__ = None
    __parent__ = None
    __children__ = {}
    __registry__ = {
        'meta': {},
        'content': {},
        'static': {},
        'menues': {},
        'widgets': {}
    }
    __acl__ = []

    def __init__(self, request):
        if self.__parent__:
            instance = self.__parent__(request)
            self.__parent__ = instance
        self.request = request

    def __getitem__(self, key):
        """
        Gets the next child resource.

        Args:
            key (str): Next URL path segment.

        Returns:
            obj: Instance of a child resource, which matches the key.

        Raises:
            KeyError: if no child resource is found.
        """
        if key in self.__children__:
            return self.__children__[key](self.request)
        raise KeyError(key)

    def __str__(self):
        """
        Renders the resource as a string.

        Returns:
            str: Resource string.
        """
        name = 'None'
        if hasattr(self.__parent__, '__name__'):
            name = self.__parent__.__name__
        return (
            "context: %s.%s\n"
            "context.__parent__: %s\n"
            "context.__children__: %s\n"
            "context.registry:\n%s"
        ) % (
            self.__class__.__module__, self.__class__.__name__,
            name,
            self.__children__,
            self.registry,
        )

    @classmethod
    def add_child(cls, val):
        """
        Adds a child resource to this resource.

        Args:
            val (class): Class of child resource.

        Returns:
            None.

        Examples:
            >>> ParentResource.add_child(ChildResource)
        """
        val.__parent__ = cls
        cls.__children__[val.__dict__['__name__']] = val

    @classmethod
    def merge_registry(cls, orig_dict, new_dict):
        """
        Recursively merges dict-like objects.

        Note:
            If a value in new_dict is `{}`, the key is removed in orig_dict

        Args:
            orig_dict (dict): Original dictionary to be merged with.
            new_dict (dict): New dictionary to be merged.

        Returns:
            dict: Merged dict.

        Examples:
            >>> orig_dict = {
            ...     'A': {
            ...         'A1': 'A1',
            ...         'A2': 'A2'
            ...     },
            ...     'B': 'B'
            ... }
            >>> new_dict = {
            ...     'A': {
            ...         'A2': 'XX'
            ...     },
            ...     'B': {},
            ...     'C': 'C'
            ... }
            >>> print(cls.merge_registry(orig_dict, new_dict))
            {
                'A': {
                    'A1': 'A1',
                    'A2': 'XX'
                },
                'C': 'C'
            }
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
        """
        Decorator function to extend the registry.

        The `__registry__` class attribute might contain a dictionary or a
        property function returning a dictionary. By extending the registry,
        the original class attribute is replaced by a property function, which
        merges the original registry with a new registry returned by `func`.
        Registries might be extended several times.

        Args:
            func (function): Function extending the registry.

        Returns:
            None
        """
        _orig_reg = cls.__registry__

        def _registry_extension(self):
            orig_dict = _orig_reg
            if isinstance(orig_dict, property):
                orig_dict = orig_dict.fget(self)
            return cls.merge_registry(dict(orig_dict), func(self))
        cls.__registry__ = property(_registry_extension)

    @property
    def registry(self):
        """
        Gets the current registry of the resource.

        The registry is retrieved by merging the (possibly extended) registry
        with all (possibly extended) registries of the current resource branch
        back to the root parent once and is cached. Additional calls will
        return the cached registry.

        Returns:
            dict: Current registry
        """
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
        """
        Returns an autovivid dictionary for easy extension of the registry.

        Returns:
            dict: Autovivid dictionary

        Examples:
            >>> reg = self.dict()
            >>> print(reg['create']['key']['path'] = 'onthefly')
            {
                'create': {
                    'key': {
                        path': 'onthefly'
                    }
                }
            }
        """
        return defaultdict(self.dict)


class WebRootFactory(object):
    """
    Root resource factory for web service.

    Args:
        request (pyramid.request.Request): Current request.

    Returns:
        BackendResource: If user is logged in
        FrontendResource: If user is not logged in
    """
    def __new__(cls, request):
        if request.user:
            return BackendResource(request)
        return FrontendResource(request)


class ApiRootFactory(ResourceBase):
    """
    Root resource factory for api service.

    Args:
        request (pyramid.request.Request): Current request.

    Access:
        No permissions (not needed for api views)
    """
    __name__ = ""
    __parent__ = None
    __children__ = {}
    __acl__ = []


class FrontendResource(ResourceBase):
    """
    Root resource for users not logged in ("frontend").

    Args:
        request (pyramid.request.Request): Current request.

    Access:
        No permissions (not needed for page views)
    """
    __name__ = ""
    __parent__ = None
    __children__ = {}
    __acl__ = []


class BackendResource(ResourceBase):
    """
    Root resource for users logged in ("backend").

    Args:
        request (pyramid.request.Request): Current request.

    Access:
        Authenticated: read
    """
    __name__ = ""
    __parent__ = None
    __children__ = {}
    __acl__ = [
        (Allow, Authenticated, 'read')
    ]


class ProfileResource(ResourceBase):
    """
    Profile resource for managing the user profile.

    Args:
        request (pyramid.request.Request): Current request.

    Access:
        Authenticated: read
    """
    __name__ = "profile"
    __parent__ = BackendResource
    __children__ = {}
    __acl__ = [
        (Allow, Authenticated, 'read')
    ]


class DebugResource(ResourceBase):
    """
    Root resource for debug views.

    Note:
        To be included in the resource tree in development environment only.

    Args:
        request (pyramid.request.Request): Current request.

    Access:
        No permissions (not needed for debug views)
    """
    __name__ = "debug"
    __parent__ = BackendResource
    __registry__ = {}
    __acl__ = []


class NewsResource(ResourceBase):
    """
    Example for a news resource for news content provided by the registry.

    Args:
        request (pyramid.request.Request): Current request.

    Access:
        No permissions
    """
    __name__ = "news"
    __parent__ = BackendResource
    __children__ = {}
    __registry__ = {}
    __acl__ = []

    def __getitem__(self, key):
        if key in self.registry['content']['news']:
            article = ArticleResource(self.request, key)
            self.__children__[key] = article
            article.__name__ = key
            return article
        raise KeyError(key)


class ArticleResource(ResourceBase):
    """
    Example for an article resource for news content provided by the registry.

    Args:
        request (pyramid.request.Request): Current request.
        id (int): Article id.

    Access:
        No permissions
    """
    __name__ = "article"
    __parent__ = NewsResource
    __children__ = {}
    __registry__ = {}
    __acl__ = []

    def __init__(self, request, id):
        super(ArticleResource, self).__init__(request)
        self.article = self.registry['content']['news'][id]
