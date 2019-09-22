# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

"""
Dictionary Merge Tests
"""

from pyramid.testing import DummyRequest

from ..base import UnitTestBase

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


class TestResources(UnitTestBase):

    def test_dictionary_merge_secondlevel_original_persistance(self):
        '''
        Dictionary merge: Does value from original second-level dictionary
        persist?
        '''
        orig_dict = {
            'A': {
                'A1': 'A1',
                'A2': 'A2'
            },
            'B': 'B'
        }
        new_dict = {
            'A': {
                'A2': 'XX'
            },
            'B': {},
            'C': 'C'
        }
        result_dict = ResourceBase.merge_registry(orig_dict, new_dict)
        self.assertEqual(result_dict['A']['A1'], 'A1')

    def test_dictionary_merge_secondlevel_new_persistance(self):
        '''
        Dictionary merge: Does value from new second-level dictionary persist
        over value of original second-level dictionary?
        '''
        orig_dict = {
            'A': {
                'A1': 'A1',
                'A2': 'A2'
            },
            'B': 'B'
        }
        new_dict = {
            'A': {
                'A2': 'XX'
            },
            'B': {},
            'C': 'C'
        }
        result_dict = ResourceBase.merge_registry(orig_dict, new_dict)
        self.assertEqual(result_dict['A']['A2'], 'XX')

    def test_dictionary_merge_firstlevel_deletion(self):
        '''
        Dictionary merge: Is value being deleted if an empty value {} is
        assigned in new dictionary?
        '''

        orig_dict = {
            'A': {
                'A1': 'A1',
                'A2': 'A2'
            },
            'B': 'B'
        }
        new_dict = {
            'A': {
                'A2': 'XX'
            },
            'B': {},
            'C': 'C'
        }
        result_dict = ResourceBase.merge_registry(orig_dict, new_dict)
        self.assertEqual(result_dict['B'], {})

    def test_dictionary_merge_firstlevel_new_persistance(self):
        '''
        Dictionary merge: Does value from new first-level dictionary persist
        over value of original first-level dictionary?
        '''

        orig_dict = {
            'A': {
                'A1': 'A1',
                'A2': 'A2'
            },
            'B': 'B'
        }
        new_dict = {
            'A': {
                'A2': 'XX'
            },
            'B': {},
            'C': 'C'
        }
        result_dict = ResourceBase.merge_registry(orig_dict, new_dict)
        self.assertEqual(result_dict['C'], 'C')

    # class TestResource(ResourceBase):
    # ... resources.py
    # @TestResource.extend_registry
    # ... include.py
    # TestResource.registry
    # -> !

    def test_resourcebase_init(self):
        """
        test ResourceBase.init
        """
        self.request = DummyRequest()

        rb = ResourceBase(self.request)
        rb

    def test_resourcebase_init_parent(self):
        """
        test ResourceBase.init with parent

        """
        self.request = DummyRequest()

        rbc = ResourceBaseChildMock(self.request)
        rbc

    def test_getitem_KeyError(self):
        """
        test ResourceBase.__getitem__
        """
        self.request = DummyRequest()

        rbc = ResourceBaseChildMock(self.request)

        with self.assertRaises(KeyError) as context:
            rbc.__getitem__('foo')

        self.assertTrue('foo' in context.exception)

    def test_getitem_child(self):
        """
        test ResourceBase.__getitem__
        """
        ResourceBaseMock.add_child(ResourceBaseChildMock)
        self.request = DummyRequest()

        rb = ResourceBaseMock(self.request)

        self.assertEqual('newschild', rb.__getitem__('newschild').__name__)

    def test_add_child(self):
        """
        test ResourceBase.add_child
        """
        self.request = DummyRequest()

        ResourceBaseMock.add_child(ResourceBaseChildMock)

        self.assertTrue('newschild' in ResourceBaseMock.__children__)
        self.assertIsInstance(
            ResourceBaseMock, ResourceBaseChildMock.__parent__.__class__)
        self.assertEqual(
            ResourceBaseChildMock.__parent__.__name__,
            'ResourceBaseMock'
        )

    def test_resourcebase__str__(self):
        """
        test ResourceBase.__str__
        """
        self.request = DummyRequest()
        rb = ResourceBaseChildMock(self.request)
        res = rb.__str__()

        self.assertTrue("context" in res)
        self.assertTrue(
            (
                "collecting_society_portal.tests.unit.resources."
                "ResourceBaseChildMock\n"
            ) in res)
        self.assertTrue("context.__parent__: news\n" in res)
        self.assertTrue("context.__children__: {   }\n" in res)
        self.assertTrue("context.registry" in res)


class TestWebRootFactory(UnitTestBase):

    def test_webrootfactory_frontend(self):
        """
        test webrootfactory frontend
        """
        self.request = DummyRequest()
        self.config.testing_securitypolicy(userid=None, permissive=False)
        fr = WebRootFactory(self.request)
        self.assertIsInstance(fr, FrontendResource)

    def test_webrootfactory_backend(self):
        """
        test webrootfactory backend
        """
        self.request = DummyRequest()
        self.config.testing_securitypolicy(userid=1, permissive=True)
        br = WebRootFactory(self.request)
        self.assertIsInstance(br, BackendResource)
