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
        'company_src_id': fields.many2one('res.company', 'On behalf of', required=True),
        'journal_src_id': fields.many2one('account.journal', 'Sale Journal',
            domain=[('type', '=', 'sale')], required=True),
        'account_src_ids': fields.one2many('account.invoice.behalf_of.account_src', 'behalf_of_id', 'Accounts Mapping'),

        'company_dest_id': fields.many2one('res.company', 'Billing Company', required=True),
        'journal_dest_id': fields.many2one('account.journal', 'Miscellaneous Operation Journal',
            domain=[('type', '=', 'general')], required=True),
        'account_dest_ids': fields.one2many('account.invoice.behalf_of.account_dest', 'behalf_of_id', 'Accounts Mapping'),

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

class AcccountInvoiceBehalfOfAccountSource(osv.osv):
    _name = 'account.invoice.behalf_of.account_src'
    _description = 'Accounts Mapping'
    _rec_name = 'behalf_of_id'

    _columns = {
        'behalf_of_id': fields.many2one('account.invoice.behalf_of', 'Billing on behalf of', required=True, ondelete='cascade'),
        'company_src_id': fields.related('behalf_of_id', 'company_src_id', type='many2one', relation='res.company', string='Company', readonly=True),
        'account_src_id': fields.many2one('account.account', 'Source Account', required=True),
        'account_dest_id': fields.many2one('account.account', 'Destination Account', required=True),
    }
AcccountInvoiceBehalfOfAccountSource()

class AcccountInvoiceBehalfOfAccountDestination(osv.osv):
    _name = 'account.invoice.behalf_of.account_dest'
    _description = 'Accounts Mapping'
    _rec_name = 'behalf_of_id'

    _columns = {
        'behalf_of_id': fields.many2one('account.invoice.behalf_of', 'Billing on behalf of', required=True, ondelete='cascade'),
        'company_src_id': fields.related('behalf_of_id', 'company_src_id', type='many2one', relation='res.company', string='On behalf of', readonly=True),
        'company_dest_id': fields.related('behalf_of_id', 'company_dest_id', type='many2one', relation='res.company', string='Billing Company', readonly=True),
        'account_src_id': fields.many2one('account.account', 'Source Account', required=True),
        'account_dest_id': fields.many2one('account.account', 'Destination Account', required=True),
    }
AcccountInvoiceBehalfOfAccountDestination()

class AccountInvoice(osv.osv):
    _inherit = 'account.invoice'

    _columns = {
        'behalf_of_id': fields.many2one('account.invoice.behalf_of', 'Billing Company'),
    }
AccountInvoice()
