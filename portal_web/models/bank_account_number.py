# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

import logging

from . import Tdb

log = logging.getLogger(__name__)


class BankAccountNumber(Tdb):
    """
    Model wrapper for Tryton model object 'bank.account.number'.
    """

    __name__ = 'bank.account.number'

    @classmethod
    def search_by_number(cls, number):
        """
        Searches a bank account number by number.

        Args:
            number (str): Number of bank account number.

        Returns:
            obj: Bank account number.
            None: If no match is found.
        """
        if number is None:
            return None
        result = cls.get().search([('number', '=', number)])
        return result[0] if result else None

    @classmethod
    def create(cls, party, vlist):
        """
        Creates bank account numbers.

        Currently only the type IBAN is implemented.

        2DO: Implement other types.

        Cascades:
            Creates a bank with the bic as name if not existant.

        Args:
            vlist (list): List of dictionaries with attributes of a web user.
                [
                    {
                        'type': str (required),
                        'bic': str (required),
                        'number': str (required)
                    },
                    {
                        ...
                    }
                ]

        Returns:
            list (obj[bank.account.number]): List of created bank account
                numbers.
            None: If no object was created.

        Raises:
            KeyError: If required field is missing.
            NotImplementedError: If type is not implemented.
        """
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

            # type iban
            if values['type'] == 'iban':
                if 'number' not in values:
                    raise KeyError('number is missing')
                bank_account_numbers = cls.search_by_number(values['number'])
                # skip creation if number already exists
                if bank_account_numbers:
                    log.debug(
                        'bank account number already exists:\n{}'.format(
                            values
                        )
                    )
                    continue

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

            # type not implemented
            else:
                raise NotImplementedError(
                    'bank account number type not implemented.'
                )

        return cvlist or None
