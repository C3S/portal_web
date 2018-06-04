# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

"""
Dictionary Merge Tests
"""

from ..base import UnitTestBase

from ....services import iban


class TestIban(UnitTestBase):

    def test_iban(self):
        '''
        Assemble an IBAN
        '''
        code, bank, account = "DE", "12345678", "123456789"
        german_iban = iban.create_iban(code, bank, account)
        self.assertEqual(german_iban, 'DE58123456780123456789')

    def test_country(self):
        '''
        Get a country name by its code
        '''
        code = "DE"
        country = iban.country_data(code)
        self.assertEqual(country.name, 'Germany')
