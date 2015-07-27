# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import logging

from . import Tdb

log = logging.getLogger(__name__)


class BankAccountNumber(Tdb):
    """
    Model wrapper for Tryton model object 'bank.account.number'
    """

    __name__ = 'bank.account.number'

    @classmethod
    @Tdb.transaction(readonly=True)
    def search_by_number(cls, number):
        """
        Searches a bank account number by number

        Args:
          number (string): number of bank account number

        Returns:
          obj: bank.account.number
          None: if no match is found
        """
        if number is None:
            return None
        result = cls.get().search([('number', '=', number)])
        return result[0] if result else None

    @classmethod
    @Tdb.transaction(readonly=False)
    def create(cls, party, vlist):
        _Party = cls.get('party.party')
        _Bank = cls.get('bank')
        _BankAccount = cls.get('bank.account')

        cvlist = []
        for values in vlist:
            if 'bic' not in values:
                    raise KeyError('bic is missing')
            if 'type' not in values:
                raise KeyError('type is missing')

            # create bank if not existing
            banks = _Bank.search([('bic', '=', values['bic'])])
            if banks:
                bank = banks[0]
            else:
                bank = _Bank(
                    bic=values['bic'],
                    party=_Party(name=values['bic'])
                )
                bank.save()

            # iban
            if values['type'] == 'iban':
                if 'number' not in values:
                    raise KeyError('number is missing')
                bank_account_numbers = cls.search_by_number(values['number'])
                if bank_account_numbers:
                    raise KeyError('number already exists')

                _bank_account = {
                    'bank': bank.id,
                    'owner': party.id,
                    'numbers': [
                        (
                            'create',
                            [{
                                'type': values['type'],
                                'number': values['number']
                            }]
                        )
                    ]
                }

                bank_accounts = _BankAccount.create([_bank_account])
                bank_account = bank_accounts[0]
                cvlist.append(bank_account.numbers[-1])
        return cvlist or []
