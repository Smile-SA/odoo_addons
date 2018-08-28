# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp.osv import orm, fields

PAYMENT_TYPES = [('I', 'Individual'), ('G', 'Grouped')]


class ResPartner(orm.Model):
    _inherit = 'res.partner'

    def _has_grouped_payments_in_progress(self, cr, uid, ids, name, arg, context=None):
        res = {}.fromkeys(ids, False)
        cr.execute("""SELECT rp.id FROM res_partner rp INNER JOIN account_invoice ai ON ai.partner_id = rp.id
        WHERE rp.id IN %s AND ai.state = 'progress_paid' AND ai.payment_type = 'G'""", (tuple(ids),))
        for row in cr.fetchall():
            res[row[0]] = True
        return res

    def _get_partner_ids_from_invoices(self, cr, uid, ids, context=None):
        partner_ids = []
        for invoice in self.browse(cr, uid, ids, context):
            if invoice.state == 'progress_paid' and invoice.payment_type == 'G':
                partner_ids.append(invoice.partner_id.id)
        return partner_ids

    _columns = {
        'payment_type': fields.selection(PAYMENT_TYPES, "Payment Type", required=True),
        'payment_mode_id': fields.many2one('account.payment.mode', "Payment Mode", required=True),
        'has_grouped_payments_in_progress': fields.function(_has_grouped_payments_in_progress, method=True, type='boolean', store={
            'account.invoice': (_get_partner_ids_from_invoices, ['state'], 10),
        }, string="Has grouped payments in progress"),
    }

    _defaults = {
        'payment_type': 'I',
    }
