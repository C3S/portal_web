# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

"""
Dictionary Merge Tests
"""

from ....services import iban


class TestIban:
    """
    Iban test class
    """

    def test_iban(self):
        """
        Assemble an IBAN
        """
        code, bank, account = "DE", "12345678", "123456789"
        german_iban = iban.create_iban(code, bank, account)
        assert german_iban == 'DE58123456780123456789'

    def test_country(self):
        """
        Get a country name by its code
        """
        code = "DE"
        country = iban.country_data(code)
        assert country.name == 'Germany'
