# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

"""
Dictionary Merge Tests
"""

from ..base import UnitTestBase

from ...resources import ResourceBase

class TestResources(UnitTestBase):

    def test_dictionary_merge_secondlevel_original_persistance(self):
        '''
        Dictionary merge: Does value from original second-level dictionary persist?
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
        Dictionary merge: Does value from new second-level dictionary persist over value of original second-level dictionary?
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
        Dictionary merge: Is value being deleted if an empty value {} is assigned in new dictionary?
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
        Dictionary merge: Does value from new first-level dictionary persist over value of original first-level dictionary?
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