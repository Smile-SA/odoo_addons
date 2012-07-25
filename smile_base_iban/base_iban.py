# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import string

from osv import osv, fields
from tools.translate import _


def compute_acc_key(bank_code, branch_code, account_number):
    def convert_to_integer(account_number):
        account_number = list(account_number)
        if account_number:
            letter_to_number = dict(zip("ABCDEFGHIJKLMNOPQR?STUVWXYZ", "123456789123456789123456789"))
            for index, character in enumerate(account_number):
                if character in letter_to_number:
                    account_number[index] = letter_to_number[character]
        return ''.join(account_number)
    account_number = convert_to_integer(account_number)
    return str(97 - ((89 * int(bank_code) + 15 * int(branch_code) + 3 * int(account_number)) % 97))


def compute_iban_check_digits(bban, country_code):
    def convert_to_integer(code):
        code = list(code)
        letters_to_numbers = dict([(l, str(i + 10)) for i, l in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ')])
        for index, character in enumerate(code):
            for index, character in enumerate(code):
                if character in letters_to_numbers:
                    code[index] = letters_to_numbers[character]
        return int(''.join(code))
    return str(98 - convert_to_integer(bban + country_code + '00') % 97).rjust(2, '0')


def compute_iban_from_bban(bban, country_code):
    country_code = country_code.upper()
    if country_code != 'FR':
        raise osv.except_osv(_('Error'), _('The function is implemented only for French Bank Account!'))
    return country_code + compute_iban_check_digits(bban, country_code) + bban


class ResPartnerBank(osv.osv):
    _inherit = "res.partner.bank"

    def _get_acc_key(self, cr, uid, ids, name, arg, context=None):
        res = {}.fromkeys(ids, '')
        for bank_account in self.browse(cr, uid, ids, context):
            if bank_account.country_id \
                    and bank_account.country_id.code.upper() == 'FR' \
                    and bank_account.bank.code \
                    and bank_account.branch_code \
                    and bank_account.acc_number:
                res[bank_account.id] = compute_acc_key(bank_account.bank.code, bank_account.branch_code, bank_account.acc_number)
        return res

    def _set_acc_key(self, cr, uid, ids, name, value, arg, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        cr.execute("UPDATE res_partner_bank SET acc_key = %s WHERE id IN %s", (value or '', tuple(ids)))
        return True

    def _get_partner_bank_ids_from_banks(self, cr, uid, ids, context=None):
        return self.pool.get('res.partner.bank').search(cr, uid, [('bank', 'in', ids)], context=context)

    _columns = {
        'bank_code': fields.related('bank', 'code', type='char', size=5, string='Bank Code', readonly=True, store=True),
        'branch_code': fields.char('Branch Code', size=5),
        'acc_number': fields.char('Account Number', size=11),  # Resize existing field
        'acc_key': fields.function(_get_acc_key, fnct_inv=_set_acc_key, method=True, type='char', size=2, string='Account Key', store={
            'res.partner.bank': (lambda self, cr, uid, ids, context: ids, ['bank', 'branch_code', 'acc_number'], 5),
            'res.bank': (_get_partner_bank_ids_from_banks, ['code'], 5),
        }),
        'iban': fields.char('IBAN', size=34, readonly=False, help=""),
        'bic': fields.related('bank', 'bic', type='char', size=11, string='BIC/Swift code', readonly=True, store=True),
    }

    _defaults = {
        'state': 'iban',
    }

    def get_iban_from_bban(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}.fromkeys(ids, '')
        for bank_account in self.browse(cr, uid, ids, context):
            if bank_account.iban:
                res[bank_account.id] = bank_account.iban
                continue
            elif bank_account.bank and bank_account.bank.code and bank_account.branch_code and bank_account.acc_number:
                bban = bank_account.bank.code + bank_account.branch_code + bank_account.acc_number + bank_account.acc_key
                country_code = bank_account.country_id.code
                res[bank_account.id] = compute_iban_from_bban(bban, country_code)
        return res

    def button_get_iban_from_bban(self, cr, uid, ids, context=None):
        for bank_account_id, iban in self.get_iban_from_bban(cr, uid, ids, context).items():
            if iban:
                self.write(cr, uid, bank_account_id, {'iban': iban}, context)
        return True

    def button_get_bban_from_iban(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for bank_account in self.browse(cr, uid, ids, context):
            iban = bank_account.iban
            if iban:
                if iban[: 2].upper() != 'FR':
                    raise osv.except_osv(_('Error'), _('The function is implemented only for French Bank Account!'))
                bank_code = iban[4: 9]
                if bank_account.bank_code != bank_code:
                    if bank_account.bank_code:
                        raise osv.except_osv(_('Error'), _('Bank code does not match with IBAN!'))
                    else:
                        bank_account.bank.write({'code': bank_code})
                bank_account.write({
                    'branch_code': iban[9: 14],
                    'acc_number': iban[14: -2],
                    'acc_key': iban[-2:],
                    'country_id': self.pool.get('res.country').search(cr, uid, [('code', 'ilike', iban[: 2])], context=context)[0],
                }, context)
        return True

    def create(self, cr, uid, vals, context=None):
        res_id = super(ResPartnerBank, self).create(cr, uid, vals, context)
        if vals['state'] == 'bank':
            self.button_get_iban_from_bban(cr, uid, res_id, context)
        elif vals['state'] == 'iban':
            self.button_get_bban_from_iban(cr, uid, res_id, context)
        return res_id

    def onchange_bank(self, cr, uid, ids, bank_id, iban, state, context=None):
        res = {'value': {'bank': False, 'bic': '', 'bank_code': ''}}
        if bank_id:
            bank = self.pool.get('res.bank').browse(cr, uid, bank_id, context)
            if state == 'iban' and bank.code and iban and iban[4: 9] != bank.code:
                return {'warning': {
                    'title': _('Warning!'),
                    'message': _('Bank code does not match with IBAN!'),
                }, 'value': {'bank': False}}
            res['value'] = {'bank': bank_id, 'bic': bank.bic, 'bank_code': bank.code}
        return res

ResPartnerBank()


class ResBank(osv.osv):
    _inherit = "res.bank"

    def _check_bic(self, cr, uid, bic, context=None):

        assert isinstance(bic, basestring), 'bic must be a string!'
        if len(bic) not in (8, 11):
            raise osv.except_osv(_('Error'), _('BIC/SWIFT code has 8 characters if it is the national headquarters of the bank, 11 otherwise!'))

        def _check_bank_code(bank_code):
            for char in bank_code:
                if char not in string.ascii_uppercase:
                    raise osv.except_osv(_('Error'), _('Wrong bank code! The 4 first characters in BIC/SWIFT code must be alphabetic.'))

        def _check_country_code(country_code):
            if self.pool.get('res.country').search(cr, uid, [('code', 'ilike', country_code)], context=context, count=True):
                return True
            raise osv.except_osv(_('Error'), _('Wrong country code! The 4th and 5th characters in BIC/SWIFT code do not match with a country code.'))

        def _check_localisation_code(localisation_code):
            for char in localisation_code:
                if char not in string.ascii_uppercase + string.digits:
                    raise osv.except_osv(_('Error'), _('Wrong localisation code! The 6th and 7th characters in BIC/SWIFT code must be alphanumeric.'))

        def _check_branch_code(branch_code):
            if branch_code:
                for char in branch_code:
                    if char not in string.ascii_uppercase + string.digits:
                        raise osv.except_osv(_('Error'), _('Wrong branch code! The 3 last characters in BIC/SWIFT code must be alphanumeric.'))

        _check_bank_code(bic[: 4])
        _check_country_code(bic[4: 6])
        _check_localisation_code(bic[6: 8])
        _check_branch_code(bic[8:])
        return True

    def create(self, cr, uid, vals, context=None):
        vals = vals or {}
        if vals.get('bic'):
            vals['bic'] = vals['bic'].upper()
            self._check_bic(cr, uid, vals['bic'], context)
        return super(ResBank, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        vals = vals or {}
        if vals.get('bic'):
            vals['bic'] = vals['bic'].upper()
            self._check_bic(cr, uid, vals['bic'], context)
        return super(ResBank, self).write(cr, uid, ids, vals, context)

ResBank()
