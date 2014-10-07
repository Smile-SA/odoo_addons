# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
#                       author cyril.gaspard@smile.fr
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
from openerp.osv import orm


class Invoice(orm.Model):
    _inherit = 'account.invoice'

    def invoice_pay_customer(self, cr, uid, ids, context=None):
        context = context or {}
        if not ids:
            return []
        inv = self.browse(cr, uid, ids[0], context=context)
        res = super(Invoice, self).invoice_pay_customer(cr, uid, ids, context=context)
        res['context']['default_journal_id'] = inv and inv.payment_terms_id and \
            inv.payment_terms_id.property_account_journal and inv.payment_terms_id.property_account_journal.id or False,
        return res
