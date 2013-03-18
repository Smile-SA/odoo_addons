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

from osv import osv, fields


class AcccountInvoiceBehalfOf(osv.osv):
    _name = 'account.invoice.behalf_of'
    _description = 'Billing on behalf of'
    _rec_name = 'company_dest_id'

    _columns = {
        'company_src_id': fields.many2one('res.company', 'On behalf of', required=True, ondelete='cascade'),
        'fiscal_position_src_id': fields.many2one('account.fiscal.position', 'Fiscal Position', required=True, ondelete='restrict',
                                                  domain=[('type', '=', 'behalf')], help="Only accounts and journals mapping"),

        'company_dest_id': fields.many2one('res.company', 'Billing Company', required=True, ondelete='cascade'),
        'account_model_dest_id': fields.many2one('account.model', 'Account Move Model', required=True, ondelete='restrict',
                                                 help="Indicate debit / credit line by adding an amount different from zero in the right column."),

        'partner_dest_id': fields.related('company_dest_id', 'partner_id', type='many2one', relation='res.partner',
                                          string='Billing Partner', readonly=True, store=True),
        'bank_account_id': fields.many2one('res.partner.bank', 'Bank Account', required=False),
    }

    def name_get(self, cr, uid, ids, context=None):
        res = []
        if isinstance(ids, (int, long)):
            ids = [ids]
        for item in self.read(cr, uid, ids, ['company_dest_id'], context, '_classic_read'):
            res.append((item['id'], item['company_dest_id'][1]))
        return res

AcccountInvoiceBehalfOf()


class AccountInvoice(osv.osv):
    _inherit = 'account.invoice'

    _columns = {
        'behalf_of_id': fields.many2one('account.invoice.behalf_of', 'Billing Company', readonly=True, states={'draft': [('readonly', False)]}),
    }

    def onchange_behalf_of_id(self, cr, uid, ids, behalf_of_id=False, company_id=False):
        if not behalf_of_id:
            return {}
        company_dest_id = self.pool.get('account.invoice.behalf_of').read(cr, uid, behalf_of_id, ['company_dest_id'],
                                                                          load='_classic_write')['company_dest_id']
        return {'domain': {'fiscal_position': [('company_id', '=', company_id), ('company_dest_id', '=', company_dest_id)]}}

AccountInvoice()
