# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

"""
Resources Tests
"""

import pytest

from ...resources import (
    BackendResource,
    FrontendResource,
    ResourceBase,
    WebRootFactory
)


class ResourceBaseMock(ResourceBase):
    """
    mock resource base object
    """
    __name__ = "news"
    __parent__ = None
    __children__ = {}
    __registry__ = {}
    __acl__ = []


class ResourceBaseChildMock(ResourceBase):
    """
    mock resource base child object

    * has __parent__
    * child of ResourceBaseMock
    """
    __name__ = "newschild"
    __parent__ = ResourceBaseMock
    __children__ = {}
    __registry__ = {}
    __acl__ = []


@pytest.fixture(scope="module")
def orig_dict():
    return {
        'A': {
            'A1': 'A1',
            'A2': 'A2'
        },
        'B': 'B'
    }


@pytest.fixture(scope="module")
def new_dict():
    return {
        'A': {
            'A2': 'XX'
        },
        'B': {},
        'C': 'C'
    }


class TestResources:
    """
    Resource test class
    """

    def test_dictionary_merge_secondlevel_original_persistance(
            self, orig_dict, new_dict):
        """
        Dictionary merge: Does value from original second-level dictionary
        persist?
        """
        result_dict = ResourceBase.merge_registry(orig_dict, new_dict)
        assert result_dict['A']['A1'] == 'A1'

    def test_dictionary_merge_secondlevel_new_persistance(
            self, orig_dict, new_dict):
        """
        Dictionary merge: Does value from new second-level dictionary persist
        over value of original second-level dictionary?
        """
        result_dict = ResourceBase.merge_registry(orig_dict, new_dict)
        assert result_dict['A']['A2'] == 'XX'

    def test_dictionary_merge_firstlevel_deletion(
            self, orig_dict, new_dict):
        """
        Dictionary merge: Is value being deleted if an empty value {} is
        assigned in new dictionary?
        """
        result_dict = ResourceBase.merge_registry(orig_dict, new_dict)
        assert result_dict['B'] == {}

    def test_dictionary_merge_firstlevel_new_persistance(
            self, orig_dict, new_dict):
        """
        Dictionary merge: Does value from new first-level dictionary persist
        over value of original first-level dictionary?
        """
        result_dict = ResourceBase.merge_registry(orig_dict, new_dict)
        assert result_dict['C'] == 'C'

    def test_resourcebase_init(self, pyramid):
        """
        test ResourceBase.init
        """
        resource_base = ResourceBase(pyramid.request)
        assert resource_base

    def test_resourcebase_init_parent(self, pyramid):
        """
        test ResourceBase.init with parent
        """
        resource_base_child = ResourceBaseChildMock(pyramid.request)
        assert resource_base_child

    def test_getitem_KeyError(self, pyramid):
        """
        test ResourceBase.__getitem__ KeyError
        """
        resource_base_child = ResourceBaseChildMock(pyramid.request)
        with pytest.raises(KeyError) as excinfo:
            resource_base_child.__getitem__('foo')
        assert 'foo' in str(excinfo.value)

    def test_getitem_child(self, pyramid):
        """
        test ResourceBase.__getitem__ child
        """
        ResourceBaseMock.add_child(ResourceBaseChildMock)
        resource_base = ResourceBaseMock(pyramid.request)
        assert resource_base.__getitem__('newschild').__name__ == 'newschild'

    def test_add_child(self):
        """
        test ResourceBase.add_child
        """
        ResourceBaseMock.add_child(ResourceBaseChildMock)
        assert 'newschild' in ResourceBaseMock.__children__
        assert isinstance(
            ResourceBaseMock, ResourceBaseChildMock.__parent__.__class__)
        assert ResourceBaseChildMock.__parent__.__name__ == 'ResourceBaseMock'

    def test_resourcebase__str__(self, pyramid):
        """
        test ResourceBase.__str__
        """
        resource_base = ResourceBaseChildMock(pyramid.request)
        string = resource_base.__str__()
        assert "context" in string
        assert (
            "portal_web.tests.unit.test_resources.ResourceBaseChildMock\n"
        ) in string
        assert "context.__parent__: news\n" in string
        assert "context.__children__: {}\n" in string
        assert "context.registry" in string


class TestWebRootFactory:
    """
    WebRootFactory test class
    """

    def test_webrootfactory_frontend(self, pyramid):
        """
        test webrootfactory frontend
        """
        pyramid.config.testing_securitypolicy(userid=None, permissive=False)
        frontend = WebRootFactory(pyramid.request)
        assert isinstance(frontend, FrontendResource)

    def test_webrootfactory_backend(self, pyramid):
        """
        test webrootfactory backend
        """
        pyramid.config.testing_securitypolicy(userid=1, permissive=True)
        backend = WebRootFactory(pyramid.request)
        assert isinstance(backend, BackendResource)
