# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
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

import time

import decimal_precision as dp
import netsvc
from osv import osv, fields


class PaymentMode(osv.osv):
    _name = 'payment.mode'
    _description = 'Payment Mode'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'bank_id': fields.many2one('res.partner.bank', "Bank account", required=True, ondelete='cascade'),
        'journal_id': fields.many2one('account.journal', 'Journal', required=True, ondelete='cascade', domain=[('type', '=', 'bank')]),
        'company_id': fields.many2one('res.company', 'Company', required=True, ondelete='cascade'),
        'partner_id': fields.related('company_id', 'partner_id', type='many2one', relation='res.partner', string="Partner", readonly=True),
    }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id
    }

    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        res = {'value': {'partner_id': False}}
        if not company_id:
            res['value']['partner_id'] = self.pool.get('res.company_id').read(cr, uid, company_id, ['partner_id'], context,
                                                                              '_classic_write')['partner_id']
        return res

    def get_payment_id(self, cr, uid, payment_mode_id, context=None):
        assert isinstance(payment_mode_id, (int, long)), 'payment_mode_id must be an integer!'
        payment_order_obj = self.pool.get('payment.order')
        payment_ids = payment_order_obj.search(cr, uid, [('payment_mode_id', '=', payment_mode_id), ('state', '=', 'draft')],
                                               limit=1, context=context)
        if payment_ids:
            return payment_ids[0]
        return payment_order_obj.create(cr, uid, {'payment_mode_id': payment_mode_id}, context)
PaymentMode()


class PaymentOrder(osv.osv):
    _name = 'payment.order'
    _description = 'Payment Order'

    def _get_total(self, cr, uid, ids, name, args, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}.fromkeys(ids, 0.0)
        for payment in self.browse(cr, uid, ids, context):
            if payment.voucher_ids:
                res[payment.id] = sum([voucher.amount for voucher in payment.voucher_ids], 0.0)
        return res

    _columns = {
        'name': fields.char('Reference', size=128, required=1, states={'done': [('readonly', True)]}),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ], 'State', select=True),
        'payment_mode_id': fields.many2one('payment.mode', 'Payment mode', required=True, states={'done': [('readonly', True)]}),
        'journal_id': fields.related('payment_mode_id', 'journal_id', type='many2one', relation='account.journal', string='Journal', readonly=True),
        'company_id': fields.related('payment_mode_id', 'company_id', type='many2one', relation='res.company', string='Company', readonly=True),
        'voucher_ids': fields.one2many('account.voucher', 'payment_id', 'Payment lines', states={'done': [('readonly', True)]}),
        'total': fields.function(_get_total, string="Total", method=True, type='float'),
        'total_done': fields.float("Execution Total", digits_compute=dp.get_precision('Account')),
        'user_id': fields.many2one('res.users', 'User', required=True, states={'done': [('readonly', True)]}),
        'date_prefered': fields.selection([
            ('now', 'Directly'),
            ('due', 'Due date'),
            ('fixed', 'Fixed date'),
        ], "Preferred date", change_default=True, required=True, states={'done': [('readonly', True)]}),
        'date_scheduled': fields.date('Scheduled date if fixed', states={'done': [('readonly', True)]}),
        'date_done': fields.date('Execution date', readonly=True),
        'create_date': fields.datetime('Creation date', readonly=True),
    }

    _defaults = {
        'name': lambda self, cr, uid, context = None: self.pool.get('ir.sequence').get(cr, uid, 'payment.order'),
        'user_id': lambda self, cr, uid, context = None: uid,
        'state': 'draft',
        'date_prefered': 'due',
    }

    def action_set_done(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        vals = {'state': 'done', 'date_done': time.strftime('%Y-%m-%d')}
        for payment in self.browse(cr, uid, ids, context):
            vals['total_done'] = payment.total
            payment.write(vals, context)
            if payment.company_id.post_payment_orders:
                for voucher in payment.voucher_ids:
                    wf_service.trg_validate(uid, 'account.voucher', voucher.id, 'proforma_voucher', cr)
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        voucher_ids = sum([payment['voucher_ids'] for payment in self.read(cr, uid, ids, ['voucher_ids'], context, '_classic_write')], [])
        self.pool.get('account.voucher').cancel_voucher(cr, uid, voucher_ids, context)
        return self.write(cr, uid, ids, {'state': 'cancel'}, context)

    def button_set_to_draft(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for payment_id in ids:
            wf_service.trg_delete(uid, 'payment.order', payment_id, cr)
            wf_service.trg_create(uid, 'payment.order', payment_id, cr)
        return True

    def copy(self, cr, uid, payment_id, default=None, context=None):
        default = default or {}
        default.update({
            'name': self.pool.get('ir.sequence').get(cr, uid, 'payment.order'),
            'state': 'draft',
            'voucher_ids': [],
        })
        return super(PaymentOrder, self).copy(cr, uid, payment_id, default, context)

    def onchange_payment_mode_id(self, cr, uid, ids, payment_mode_id, context=None):
        res = {'value': {'journal_id': False}}
        if payment_mode_id:
            res['value']['journal_id'] = self.pool.get('payment.mode').read(cr, uid, payment_mode_id, ['journal_id'], context,
                                                                            '_classic_write')['journal_id']
        return res
PaymentOrder()
