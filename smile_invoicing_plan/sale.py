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

from datetime import datetime
import time

import decimal_precision as dp
from osv import fields, osv
from tools.translate import _

from invoicing_plan_tools import compute_date


class sale_order(osv.osv):
    _inherit = "sale.order"

    def __init__(self, pool, cr):
        super(sale_order, self).__init__(pool, cr)
        item = ('periodic', 'Invoice from Invoicing Plan')
        if not item in self._columns['order_policy'].selection:
            self._columns['order_policy'].selection.append(item)
sale_order()


class sale_config_picking_policy(osv.osv_memory):
    _inherit = 'sale.config.picking_policy'

    def __init__(self, pool, cr):
        super(sale_config_picking_policy, self).__init__(pool, cr)
        item = ('periodic', 'Invoice Based on Invoicing Plans')
        if not item in self._columns['order_policy'].selection:
            self._columns['order_policy'].selection.append(item)
sale_config_picking_policy()


class sale_order_line_period_info(osv.osv):
    _name = "sale.order.line.period.info"
    _description = "Period Infos"

    _columns = {
        'name': fields.char('Period', size=64, required=True, readonly=True),
        'periods': fields.char('Periods', size=128),
        'invoiced': fields.boolean('Invoiced', required=False),
        'to_invoice': fields.boolean('To Invoice', required=False),
        'start_date': fields.date('Start date', required=True),
        'stop_date': fields.date('Stop date', required=True),
        'invoice_line_ids': fields.one2many('account.invoice.line', 'sale_order_line_period_info_id', 'Invoice lines', required=False),
        'order_line_id': fields.many2one('sale.order.line', 'Sale order line', required=True, ondelete='cascade'),
    }

    _defaults = {
        'invoiced': lambda * a: False,
        'to_invoice': lambda * a: False,
    }
sale_order_line_period_info()


class sale_order_line(osv.osv):
    _inherit = "sale.order.line"

    def _get_subscription_cost(self, line):
        pu = 0.0

        if not line.is_subscription:
            return pu

        for period in range(1, line.invoicing_plan_id.commitment + 1):

            for modality in line.invoicing_plan_id.line_ids:

                # Only the first valid modality applies
                periods = [eval(p1) for p1 in modality.application_periods.replace(' ', '').split(', ')]

                if period in periods or periods == [0]:

                    for sub_mod in modality.invoicing_plan_sub_line_ids:
                    #    sub_mod = modality
                        if sub_mod.value == 'balance':
                            pu += line.price_subtotal
                        elif sub_mod.value == 'fixed':
                            pu += sub_mod.value_amount
                        else:  # elif modality.value == 'percent':
                            pu += line.price_subtotal * sub_mod.value_amount
                    break

        return pu

    def _get_invoiced_ammount(self, line):
        res = 0.0

        for period in line.line_invoice_info_ids:
            for invoice_line in period.invoice_line_ids:
                res += invoice_line.price_subtotal

        return res

    def _get_residual(self, cr, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}.fromkeys(ids, 0.0)

        for line in self.browse(cr, uid, ids, context=context):

            if not line.is_subscription:
                continue

            if line.commitment_state:
                # already cimmited
                res[line.id] = self._get_subscription_cost(line) - self._get_invoiced_ammount(line)
            else:
                if line.state == 'confirmed':
                    res[line.id] = line.price_subtotal
        return res

    def _get_sale_order_line_ids_from_invoice_lines(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        account_invoice_line_pool = self.pool.get('account.invoice.line')
        invoice_line_ids = account_invoice_line_pool.search(cr, uid, [])
        sale_order_line_names = [invline['name'] for invline in account_invoice_line_pool.read(cr, uid, invoice_line_ids)]
        return self.pool.get('sale.order.line').search(cr, uid, [('name', 'in', sale_order_line_names)])

    def _get_dates(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        for line in self.browse(cr, uid, ids):

            invoicing_plan = line.invoicing_plan_id

            commitment_end_date = compute_date(line.invoicing_start_date, invoicing_plan.commitment)
            if invoicing_plan.mode == 'pre':
                res[line.id] = {'invoicing_next_date': line.invoicing_start_date, 'commitment_end_date': commitment_end_date}
            else:
                next_date = compute_date(line.invoicing_start_date, invoicing_plan.periodicity)
                res[line.id] = {'invoicing_next_date': next_date, 'commitment_end_date': commitment_end_date}
        return res

    def _set_invoicing_next_date(self, cr, uid, ids, name, value, arg, context=None):
        if not value:
            return False
        if not isinstance(ids, list):
            ids = [ids]

        for line in self.browse(cr, uid, ids, context=context):
            cr.execute("""update sale_order_line set
                    invoicing_next_date=%s
                where
                    id=%s""", (value, line.id))

        return True

    def _set_new_commitment_date(self, cr, uid, ids, name, value, arg, context=None):
        if not value:
            return False
        if not isinstance(ids, list):
            ids = [ids]

        for line in self.browse(cr, uid, ids, context=context):
            cr.execute("""update sale_order_line set
                    commitment_end_date=%s
                where
                    id=%s""", (value, line.id))

        return True

    def _is_commited(self, cr, uid, ids, name, arg, context):
        res = {}
        for line in self.browse(cr, uid, ids):
            if not line.invoicing_next_date or not line.commitment_end_date:
                res[line.id] = False
                continue
            if datetime.strptime(line.invoicing_next_date, '%Y-%m-%d') >= datetime.strptime(line.commitment_end_date, '%Y-%m-%d'):
                res[line.id] = False
            else:
                res[line.id] = True

        return res

    def _set_commitment_state(self, cr, uid, ids, name, value, arg, context=None):
        if not value:
            return False
        if not isinstance(ids, list):
            ids = [ids]

        for line in self.browse(cr, uid, ids, context=context):
            cr.execute("""update sale_order_line set
                    commitment_state=%s
                where
                    id=%s""", (value, line.id))

        return True

    _columns = {
        'is_subscription': fields.related('product_id', 'subscription_ok', type='boolean', string='Is a subscription', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'invoicing_plan_id': fields.many2one('account.invoicing_plan', 'Invoicing Plan', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'invoicing_start_date': fields.date('Invoicing Start Date', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'detail_periods': fields.boolean('Detail periods', required=False, readonly=True, states={'draft': [('readonly', False)]}, help='If checked, the pariods are detailed in the invoice: \n Periodicity = 3, uop = months: Three lines will be appeared in the invoice '),
        'invoicing_end_date': fields.date('Invoicing End Date', readonly=True),

        'commitment_end_date': fields.function(_get_dates, fnct_inv=_set_new_commitment_date, method=True, type='date', string="Commitment End Date", store={
            'sale.order.line': (lambda self, cr, uid, ids, c={}: ids, ['invoicing_start_date'], 10)
        }, multi='dates'),

        'invoicing_next_date': fields.function(_get_dates, fnct_inv=_set_invoicing_next_date, method=True, type='date', string="Invoicing Next Date", store={
            'sale.order.line': (lambda self, cr, uid, ids, c={}: ids, ['invoicing_start_date'], 10)
        }, multi='dates'),

        'commitment_state': fields.function(_is_commited, fnct_inv=_set_commitment_state, method=True, type='boolean', string="Already commited", store={
            'sale.order.line': (lambda self, cr, uid, ids, c={}: ids, ['invoicing_next_date', 'commitment_end_date'], 10)
        }),

        'residual': fields.function(_get_residual, method=True, type='float', string="Residual", digits_compute=dp.get_precision('Sale Price'), store={
            'sale.order.line': (lambda self, cr, uid, ids, c={}: ids, ['invoicing_next_date', 'commitment_end_date'], 10)
        }),

        'line_invoice_info_ids': fields.one2many('sale.order.line.period.info', 'order_line_id', 'Invoicing period information', required=False, readonly=True),
    }

    _defaults = {
        'invoicing_plan_id': lambda * a: False,
        'invoicing_start_date': lambda * a: False,
        'commitment_end_date': lambda * a: False,
    }

    def button_change_commitment(self, cr, uid, ids, context=None):
        id_ = self.pool.get('wizard.change.commitment').create(cr, uid, {'name': ids[0]})
        res = {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.change.commitment',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_id': id_,
            'context': {'active_id': id_},
        }
        return res

    def invoicing_start_date_change(self, cr, uid, ids, start_date, invoicing_plan_id):
        res = {}
        # Have to return the end of commitment date.
        #if invoicing_plan:
        if not invoicing_plan_id:
            return res

        invoicing_plan = self.pool.get('account.invoicing_plan').browse(cr, uid, invoicing_plan_id)
        commitment_end_date = compute_date(start_date, invoicing_plan.commitment)
        if invoicing_plan.mode == 'pre':
            res['value'] = {'invoicing_next_date': start_date, 'commitment_end_date': commitment_end_date}
        else:
            next_date = compute_date(start_date, invoicing_plan.periodicity)
            res['value'] = {'invoicing_next_date': next_date, 'commitment_end_date': commitment_end_date}
        return res

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0, uom=False, qty_uos=0, uos=False,
                          name='', partner_id=False, lang=False, update_tax=True, date_order=False,
                          packaging=False, fiscal_position=False, flag=False):
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name, partner_id, lang, update_tax, date_order, packaging, fiscal_position, flag)

        if product:
            data = self.pool.get('product.product').read(cr, uid, product, ['invoicing_plan_id', 'subscription_ok'])
            invoicing_plan_id = data['invoicing_plan_id']
            subscription_ok = False
            subscription_ok = data['subscription_ok']
            if invoicing_plan_id:
                res['value'].update({'invoicing_plan_id': invoicing_plan_id[0]})
            else:
                res['value'].update({'invoicing_plan_id': False})
            res['value'].update({'is_subscription': subscription_ok})
        return res

    def copy_data(self, cr, uid, id_, default=None, context=None):
        if not default:
            default = {}
        default.update({'line_invoice_info_ids': []})
        return super(sale_order_line, self).copy_data(cr, uid, id_, default, context=context)

    def button_confirm(self, cr, uid, ids, context=None):
        ## Before confirming, check if there is no subscribtion to confirm
        ## with a sale order in a state different than 'confirmed' one.
        subscription_ids = self.search(cr, uid, [('is_subscription', '=', True), ('id', 'in', ids)])
        if subscription_ids:
            for line in self.browse(cr, uid, subscription_ids):
                if not line.invoicing_start_date:
                    raise osv.except_osv(_('Error !'), _('The invoicing start date of %s is not yet defined') % (line.name))

                if line.invoicing_plan_id:
                    # confirmation is manually for periodic order line
                    if datetime.strptime(line.order_id.date_confirm, '%Y-%m-%d') > datetime.strptime(line.invoicing_start_date, '%Y-%m-%d'):
                        raise osv.except_osv(_('Error !'), _('The invoicing start date of %s must be later than  the date of confirmation') % (line.name))
                if line.order_id.state == 'draft':
                    raise osv.except_osv(_('Error !'), _('The contract should be validated before confirm any subscription'))

        return super(sale_order_line, self).button_confirm(cr, uid, ids)

    def _get_subscriptions2invoice(self, cr, uid, ids, start_date=None, end_date=None, invoice_outof_period=False):
            line_ids = []

            if isinstance(ids, (int, long)):
                ids = [ids]

            if not start_date or not end_date:
                return line_ids

            if invoice_outof_period:
                filter += [('invoicing_next_date', '>=', start_date), ('invoicing_next_date', '<', end_date)]
            else:
                filter += [('invoicing_next_date', '<', end_date)]

            line_ids = self.search(cr, uid, filter)
            return line_ids

    def _get_sale_order_line2invoice(self, cr, uid, ids):
            if isinstance(ids, (int, long)):
                ids = [ids]
            filter_ = [('state', '=', 'confirmed'), ('is_subscription', '=', False), ('id', 'in', ids)]
            line_ids = self.search(cr, uid, filter_)
            return line_ids

    def invoice_line_create(self, cr, uid, ids, context=None):
        start_date = None
        end_date = None

        def _get_line_period_date(line):
            ## periods_info[line_start_period] = start date
            ## periods_info[line_stop_period] = end date
            ## periods_info[periods] = [sub_periods]
            ## sub_periods = (start_date, stop_date, num_period)
            ## num_period = the number of the period = f(invoicing_next_date, invoicing_start_date)

            periods_info = {}

            if line.invoicing_plan_id.mode == 'pre':
                periods_info['line_start_period'] = line.invoicing_next_date
                periods_info['line_stop_period'] = compute_date(periods_info['line_start_period'], line.invoicing_plan_id.periodicity)
            else:

                periods_info['line_start_period'] = compute_date(line.invoicing_next_date, line.invoicing_plan_id.periodicity, 'months', 'sub')
                periods_info['line_stop_period'] = line.invoicing_next_date

            periods_info['periods'] = []
            coefs = {'days': 1, 'weeks': 7, 'months': 30}
            start_date = periods_info['line_start_period']
            stop_date = compute_date(start_date, 1)

            while datetime.strptime(stop_date, '%Y-%m-%d') <= datetime.strptime(periods_info['line_stop_period'], '%Y-%m-%d'):

                timedelta = datetime.strptime(stop_date, '%Y-%m-%d') - datetime.strptime(line.invoicing_start_date, '%Y-%m-%d')
                period = int(round(float(timedelta.days + (float(timedelta.seconds) / (3600 * 24))) / coefs[line.invoicing_plan_id.uop]))
                periods_info['periods'].append((start_date, stop_date, period))
                start_date = stop_date
                stop_date = compute_date(start_date, 1)

            return periods_info

        def _get_line_pu(line):
            res = {}
            periods_info = _get_line_period_date(line)

            if not periods_info and not 'periods' in periods_info:
                return res

            for p in periods_info['periods']:

                for modality in line.invoicing_plan_id.line_ids:
                    # Only the first valid modality applies
                    pu = 0.0

                    period = p[2]

                    periods = [eval(p1) for p1 in modality.application_periods.replace(' ', '').split(', ')]

                    if period in periods or periods == [0]:

                        for sub_mod in modality.invoicing_plan_sub_line_ids:
                        #    sub_mod = modality
                            if sub_mod.value == 'balance':
                                pu = line.residual
                            elif sub_mod.value == 'fixed':
                                pu = sub_mod.value_amount
                            else:  # elif modality.value == 'percent':
                                pu = line.price_unit * sub_mod.value_amount

                            if line.detail_periods:

                                if not (p[0], p[1]) in res:
                                    res[(p[0], p[1])] = {'price_unit': {'parent': (0.0, False), 'partner': (0.0, False)}, 'period_numbers': [period]}

                                if sub_mod.partner == 'object.partner_id.id':
                                    res[(p[0], p[1])]['price_unit']['partner'] = (res[(p[0], p[1])]['price_unit']['partner'][0] + pu, True)

                                else:
                                    res[(p[0], p[1])]['price_unit']['parent'] = (res[(p[0], p[1])]['price_unit']['parent'][0] + pu, True)

                            else:
                                if not (periods_info['line_start_period'], periods_info['line_stop_period']) in res:
                                    res[(periods_info['line_start_period'], periods_info['line_stop_period'])] = {'price_unit': {'parent': (0.0, False), 'partner': (0.0, False)}, 'period_numbers': []}

                                if sub_mod.partner == 'object.partner_id.id':
                                    new_pu = res[(periods_info['line_start_period'], periods_info['line_stop_period'])]['price_unit']['partner'][0] + pu
                                    res[(periods_info['line_start_period'], periods_info['line_stop_period'])]['price_unit']['partner'] = (new_pu, True)

                                else:
                                    new_pu = res[(periods_info['line_start_period'], periods_info['line_stop_period'])]['price_unit']['parent'][0] + pu
                                    res[(periods_info['line_start_period'], periods_info['line_stop_period'])]['price_unit']['parent'] = (new_pu, True)

                                res[(periods_info['line_start_period'], periods_info['line_stop_period'])]['period_numbers'].append(period)

                        break
            return res

        if isinstance(ids, (int, long)):
            ids = [ids]

        if not context:
            context = {}

        invoice_line_ids = []

        ## get if retrieve uninvoiced periods
        invoice_outof_period = context.get('invoice_outof_period', False)

        if 'invoicing_period' in context:
            start_date = context['invoicing_period']['start_date']
            end_date = context['invoicing_period']['end_date']

        subscriptions_ids = self._get_subscriptions2invoice(cr, uid, ids, start_date, end_date, invoice_outof_period)

        no_periodic_sale_order_line_ids_to_invoice = self._get_sale_order_line2invoice(cr, uid, ids)

        for line in self.browse(cr, uid, subscriptions_ids, context):

            if line.product_id:
                a = line.product_id.product_tmpl_id.property_account_income.id
                if not a:
                    a = line.product_id.categ_id.property_account_income_categ.id
                if not a:
                    raise osv.except_osv(_('Error !'), _('There is no income account defined for this product: "%s" (id: %d)') % (line.product_id.name, line.product_id.id, ))
            else:
                prop = self.pool.get('ir.property').get(cr, uid, 'property_account_income_categ', 'product.category', context=context)
                a = prop and prop.id or False

            if not line.invoicing_next_date:
                raise osv.except_osv(_('Error !'), _('You try to invoice sale order line which have not a valid invoicing next date: %s!') % (line.name))

            uosqty = line.product_uom_qty

            if line.product_uos:
                uosqty = line.product_uos_qty or 0.0
            ## Compute price
            ## price depends on invoicing period.
            ##
            if uosqty:
                period_pu = _get_line_pu(line)

            fpos = line.order_id.fiscal_position or False
            a = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, a)
            if not a:
                raise osv.except_osv(_('Error !'), _('There is no income category account defined in default Properties for Product Category or Fiscal Position is not defined !'))

            if not period_pu:
                continue

            for period in period_pu:
                period_str = 'period: ' + period[0] + ' ' + period[1]

                invoice_line_ids = []

                if period_pu[period]['price_unit']['partner'][1]:

                    inv_id = self.pool.get('account.invoice.line').create(cr, uid, {
                        'name': line.name + ' ' + period_str,
                        'origin': line.order_id.name,
                        'account_id': a,
                        'price_unit': period_pu[period]['price_unit']['partner'][0],
                        'quantity': uosqty,
                        'discount': line.discount,
                        'uos_id': line.product_uos and line.product_uos.id or line.product_uom.id,
                        'product_id': line.product_id.id or False,
                        'invoice_line_tax_id': [(6, 0, [tax.id for tax in line.tax_id])],
                        'note': line.notes,
                        'account_analytic_id': line.order_id.project_id and line.order_id.project_id.id or False,
                    })

                    invoice_line_ids.append(inv_id)

                if period_pu[period]['price_unit']['parent'][1]:

                    inv_id = self.pool.get('account.invoice.line').create(cr, uid, {
                        'name': line.name + ' ' + period_str,
                        'origin': line.order_id.name,
                        'account_id': a,
                        'price_unit': period_pu[period]['price_unit']['partner'][0],
                        'quantity': uosqty,
                        'discount': line.discount,
                        'uos_id': line.product_uos and line.product_uos.id or line.product_uom.id,
                        'product_id': line.product_id.id or False,
                        'invoice_line_tax_id': [(6, 0, [tax.id for tax in line.tax_id])],
                        'note': line.notes,
                        'account_analytic_id': line.order_id.project_id and line.order_id.project_id.id or False,
                        'parent': True
                    })

                    invoice_line_ids.append(inv_id)

                period_info = {
                    'name': period_str,
                    'periods': str(period_pu[period]['period_numbers']),
                    'invoiced': False,
                    'to_invoice': True,
                    'start_date': period[0],
                    'stop_date': period[1],
                    'invoice_line_ids': [(6, 0, invoice_line_ids)],
                    'order_line_id': line.id,
                }

                self.pool.get('sale.order.line.period.info').create(cr, uid, period_info)

                cr.execute('insert into sale_order_line_invoice_rel (order_line_id, invoice_id) values (%s, %s)', (line.id, inv_id))

                invoice_line_ids.append(inv_id)

            invoicing_next_date_str = compute_date(line.invoicing_next_date, line.invoicing_plan_id.periodicity)
            invoicing_next_date = datetime.strptime(invoicing_next_date_str, '%Y-%m-%d')

            if line.invoicing_plan_id.term == 'fixed':
                if (line.invoicing_plan_id.mode == 'pre' and invoicing_next_date > datetime.strptime(line.commitment_end_date, '%Y-%m-%d'))\
                        or (line.invoicing_plan_id.mode == 'post' and invoicing_next_date > datetime.strptime(compute_date(line.commitment_end_date, line.invoicing_plan_id.periodicity))):
                    self.write(cr, uid, [line.id], {'invoiced': True, 'state': 'done', 'invoicing_next_date': invoicing_next_date_str})

            else:
                self.write(cr, uid, [line.id], {'invoiced': False, 'invoicing_next_date': invoicing_next_date_str})

        if no_periodic_sale_order_line_ids_to_invoice:
            invoice_line_ids += super(sale_order_line, self).invoice_line_create(cr, uid, no_periodic_sale_order_line_ids_to_invoice, context)

        return invoice_line_ids

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        order_lines = self.browse(cr, uid, ids)
        # TODO: Try to get the result by a sql query instead the following algorithm

        for order_line in order_lines:
            if not order_line.is_subscription or not order_line.invoicing_plan_id:
                continue

            for modality in order_line.invoicing_plan_id.line_ids:
                for sub_mod in modality.invoicing_plan_sub_line_ids:
                    if sub_mod.partner == 'object.partner_id.parent_id.id':
                        if not order_line.order_id.partner_id.parent_id:
                            raise osv.except_osv(_('Error !'),
                                                 _('Parent partner is needed in invoicing plan, you should configure it in partner form'))

        super(sale_order_line, self).write(cr, uid, ids, vals, context)

    def create(self, cr, uid, vals, context=None):
        return super(sale_order_line, self).create(cr, uid, vals, context)

sale_order_line()


class sale_order2(osv.osv):
    _inherit = "sale.order"

    def _invoiced(self, cr, uid, ids, name, arg, context=None):
        res = super(sale_order, self)._invoiced(cr, uid, ids, name, arg, context)
        for sale in self.browse(cr, uid, ids, context=context):
            if sale.order_policy == 'periodic':
                for line in sale.order_line:
                    if line.residual:
                        res[sale.id] = False
                        break
        return res

    def _get_sale_order_ids_from_sale_order_lines(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        return list(set([line['order_id'][0] for line in self.read(cr, uid, ids, ['order_id'])]))

    _columns = {
        'invoicing_start_date': fields.date('Invoicing Start Date', help='set to confirmation date if the field is empty', readonly=True, states={'draft': [('readonly', False)]}),
        'invoicing_next_date': fields.date('Invoicing Next Date', help='Computed after confirming contract', readonly=True),
        'periodicity': fields.integer('Periodicity', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'uop': fields.selection([('months', 'Months'), ], 'Unit Of Periods', required=True),
        'contract_ok': fields.boolean('Is contract', required=False),
        'apply_global_invoicing_periodicity': fields.boolean('Apply global periodicity', required=False),
        'order_line': fields.one2many('sale.order.line', 'order_id', 'Order Lines', readonly=True, states={'draft': [('readonly', False)], 'progress': [('readonly', False)], 'manual': [('readonly', False)]}),
    }

    _defaults = {
        'periodicity': lambda * a: 1,
        'uop': lambda * a: 'months',
    }

    def action_wait(self, cr, uid, ids, *args):
        for o in self.browse(cr, uid, ids):
            if (o.contract_ok):

                if o.invoicing_start_date:
                    if datetime.strptime(o.invoicing_start_date, '%Y-%m-%d') < datetime.strptime(datetime.strftime(datetime.now(), '%Y-%m-%d'), '%Y-%m-%d'):
                        raise osv.except_osv(_('Error !'), _('Invoicing start date must be planned in the future !'))
                    self.write(cr, uid, [o.id], {'state': 'progress', 'date_confirm': time.strftime('%Y-%m-%d'), 'invoicing_next_date': o.invoicing_start_date})
                else:
                    self.write(cr, uid, [o.id], {'state': 'progress', 'date_confirm': time.strftime('%Y-%m-%d'), 'invoicing_start_date': time.strftime('%Y-%m-%d'), 'invoicing_next_date': time.strftime('%Y-%m-%d')})

                self.pool.get('sale.order.line').button_confirm(cr, uid, [x.id for x in o.order_line], True)
                message = _("The quotation '%s' has been converted to a sales order.") % (o.name, )
                self.log(cr, uid, o.id, message)
                message = _("The invoicing next date is planned for '%s'") % (o.invoicing_start_date)
                self.log(cr, uid, o.id, message)
            else:
                return super(sale_order, self).action_wait(cr, uid, ids, args)

    def _get_current_inv(self, order):
        ## should return current invoice according to the order partner parameter
        return False

    def _get_parent_current_inv(self, order):
        ## should return current invoice according to the order parent  partner parameter
        return False

    def _make_invoice(self, cr, uid, order, lines, context=None):

        if not order.contract_ok:
            return super(sale_order, self)._make_invoice(cr, uid, order, lines, context)
        else:
            journal_obj = self.pool.get('account.journal')
            inv_obj = self.pool.get('account.invoice')
            if context is None:
                context = {}

            journal_ids = journal_obj.search(cr, uid, [('type', '=', 'sale'), ('company_id', '=', order.company_id.id)], limit=1)
            if not journal_ids:
                raise osv.except_osv(_('Error !'),
                                     _('There is no sales journal defined for this company: "%s" (id: %d)') % (order.company_id.name, order.company_id.id))
            a = order.partner_id.property_account_receivable.id
            pay_term = order.payment_term and order.payment_term.id or False
            sale_line_ids = self.pool.get('sale.order.line').search(cr, uid, [('order_id', '=', order.id)], context=context)

            to_invoice_period_ids = self.pool.get('sale.order.line.period.info').search(cr, uid, [('to_invoice', '=', True), ('invoiced', '=', False), ('order_line_id', 'in', sale_line_ids)], context=context)

            partner_lines = []
            parent_lines = []

            for p in self.pool.get('sale.order.line.period.info').browse(cr, uid, to_invoice_period_ids):
                for inv_line in p.invoice_line_ids:
                    if inv_line.parent:
                        parent_lines.append(inv_line.id)
                    else:
                        partner_lines.append(inv_line.id)
            invoice_ids = []

            if partner_lines:
                ## get invoice that corresponds with order.incoicing_next_date
                inv_id = self._get_current_inv(order)

                if inv_id:
                    # add invoice line to the invoice
                    self.pool.get('account.invoice.line').write(cr, uid, partner_lines, {'invoice_id': inv_id})
                else:

                    str_ = order.client_order_ref or order.name
                    str_ += ' Period: '
                    str_ += order.invoicing_next_date
                    str_ += '-'
                    str_ += compute_date(order.invoicing_next_date, order.periodicity)

                    inv = {
                        'name': str_,
                        'origin': order.name,
                        'type': 'out_invoice',
                        'reference': "P%dSO%d" % (order.partner_id.id, order.id),
                        'account_id': a,
                        'partner_id': order.partner_id.id,
                        'journal_id': journal_ids[0],
                        'address_invoice_id': order.partner_invoice_id.id,
                        'address_contact_id': order.partner_order_id.id,
                        'invoice_line': [(6, 0, partner_lines)],
                        'currency_id': order.pricelist_id.currency_id.id,
                        'comment': order.note,
                        'payment_term': pay_term,
                        'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
                        'date_invoice': context.get('date_invoice', False),
                        'company_id': order.company_id.id,
                        'user_id': order.user_id and order.user_id.id or False,
                        'date_invoice': order.invoicing_next_date,
                    }

                    inv_id = inv_obj.create(cr, uid, inv, context=context)
                    data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id], pay_term, time.strftime('%Y-%m-%d'))
                    if data.get('value', False):
                        inv_obj.write(cr, uid, [inv_id], data['value'], context=context)

                    inv_obj.button_compute(cr, uid, [inv_id])
                    invoice_ids.append(inv_id)

            if parent_lines:
                parent_inv_id = self._get_parent_current_inv(order)

                if parent_inv_id:
                    # add invoice line to the invoice
                    self.pool.get('account.invoice.line').write(cr, uid, parent_lines, {'invoice_id': inv_id})
                else:
                    addr = self.pool.get('res.partner').address_get(cr, uid, [order.partner_id.parent_id.id], ['delivery', 'invoice', 'contact'])
                    parent_inv = {
                        'name': order.client_order_ref or '',
                        'origin': order.name,
                        'type': 'out_invoice',
                        'reference': "P%dSO%d" % (order.partner_id.id, order.id),
                        'account_id': a,
                        'partner_id': order.partner_id.parent_id.id,
                        'journal_id': journal_ids[0],
                        'address_invoice_id': addr['invoice'],
                        'address_contact_id': addr['contact'],
                        'invoice_line': [(6, 0, parent_lines)],
                        'currency_id': order.pricelist_id.currency_id.id,
                        'comment': order.note,
                        'payment_term': pay_term,
                        'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
                        'date_invoice': context.get('date_invoice', False),
                        'company_id': order.company_id.id,
                        'user_id': order.user_id and order.user_id.id or False,
                        'date_invoice': order.invoicing_next_date,
                    }
                    parent_inv_id = inv_obj.create(cr, uid, parent_inv, context=context)
                    data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [parent_inv_id], pay_term, time.strftime('%Y-%m-%d'))
                    if data.get('value', False):
                        inv_obj.write(cr, uid, [parent_inv_id], data['value'], context=context)

                    inv_obj.button_compute(cr, uid, [parent_inv_id])
                    invoice_ids.append(parent_inv_id)

            new_next_date = compute_date(order.invoicing_next_date, order.periodicity)
            self.write(cr, uid, order.id, {'invoicing_next_date': new_next_date})

            self.pool.get('sale.order.line.period.info').write(cr, uid, to_invoice_period_ids, {'invoiced': True})

            return invoice_ids

    def action_invoice_create(self, cr, uid, ids, grouped=False, states=['confirmed', 'done', 'exception'], date_inv=False, context=None):
        res = []
        no_periodic_order_ids = []
        periodic_order_ids = []

        if context is None:
            context = {}

        invoice_non_contracts = context.get('invoice_non_contracts', True)
        for o in self.browse(cr, uid, ids, context=context):
            if not o.contract_ok:
                no_periodic_order_ids.append(o.id)
            else:
                periodic_order_ids.append(o.id)

        if no_periodic_order_ids and invoice_non_contracts:
            res = super(sale_order, self).action_invoice_create(cr, uid, no_periodic_order_ids, grouped, states, date_inv, context)

        invoice_contracts = context.get('invoice_contracts', False)
        if not invoice_contracts:
            return res

        invoices = {}
        invoice_ids = []
        ids = periodic_order_ids
        picking_obj = self.pool.get('stock.picking')
        invoice = self.pool.get('account.invoice')
        obj_sale_order_line = self.pool.get('sale.order.line')
        if context is None:
            context = {}
        # If date was specified, use it as date invoiced, usefull when invoices are generated this month and put the
        # last day of the last month as invoice date
        if date_inv:
            context['date_inv'] = date_inv
        for o in self.browse(cr, uid, ids, context=context):
            lines = []
            for line in o.order_line:
                if line.invoiced:
                    continue
                elif (line.state in states):
                    lines.append(line.id)
            created_lines = obj_sale_order_line.invoice_line_create(cr, uid, lines, context)
            if created_lines:
                invoices.setdefault(o.partner_id.id, []).append((o, created_lines))
        if not invoices:
            return invoice_ids
        for val in invoices.values():
            if grouped:
                res = self._make_invoice(cr, uid, val[0][0], reduce(lambda x, y: x + y, [l for o, l in val], []), context=context)
                invoice_ref = ''
                for o, l in val:
                    invoice_ref += o.name + '|'
                    self.write(cr, uid, [o.id], {'state': 'progress'})
                    if o.order_policy == 'picking':
                        picking_obj.write(cr, uid, map(lambda x: x.id, o.picking_ids), {'invoice_state': 'invoiced'})
                    for id_ in res:
                        cr.execute('insert into sale_order_invoice_rel (order_id, invoice_id) values (%s, %s)', (o.id, id_))
                        invoice.write(cr, uid, res, {'origin': invoice_ref, 'name': invoice_ref})
            else:
                for order, il in val:
                    res = self._make_invoice(cr, uid, order, il, context=context)
                    invoice_ids += res
                    self.write(cr, uid, [order.id], {'state': 'progress'})
                    if order.order_policy == 'picking':
                        picking_obj.write(cr, uid, map(lambda x: x.id, order.picking_ids), {'invoice_state': 'invoiced'})

                    for id_ in res:
                        cr.execute('insert into sale_order_invoice_rel (order_id, invoice_id) values (%s, %s)', (o.id, id_))
        return invoice_ids

    # if mode == 'finished':
    #   returns True if all lines are done, False otherwise
    # if mode == 'canceled':
    #   returns True if there is at least one canceled line, False otherwise
    def test_state(self, cr, uid, ids, mode, *args):
        assert mode in ('finished', 'canceled'), _("invalid mode for test_state")
        finished = True
        canceled = False
        notcanceled = False
        write_done_ids = []
        write_cancel_ids = []
        for order in self.browse(cr, uid, ids, context={}):
            for line in order.order_line:
                if (not line.procurement_id) or (line.procurement_id.state == 'done'):
                    if line.state != 'done' and not line.is_subscription:
                        write_done_ids.append(line.id)
                else:
                    finished = False
                if line.procurement_id:
                    if (line.procurement_id.state == 'cancel'):
                        canceled = True
                        if line.state != 'exception':
                            write_cancel_ids.append(line.id)
                    else:
                        notcanceled = True
        if write_done_ids:
            self.pool.get('sale.order.line').write(cr, uid, write_done_ids, {'state': 'done'})
        if write_cancel_ids:
            self.pool.get('sale.order.line').write(cr, uid, write_cancel_ids, {'state': 'exception'})

        if mode == 'finished':
            return finished
        elif mode == 'canceled':
            return canceled
            if notcanceled:
                return False
            return canceled

    def action2_invoice_create(self, cr, uid, ids, grouped=False, states=['confirmed', 'done', 'exception'], date_inv=False, context=None):
        invoice_ids = []
        for sale_order in self.browse(cr, uid, ids):
            inv_id = self.action_invoice_create(cr, uid, [sale_order.id], grouped, states, date_inv, context)
            if inv_id and sale_order.order_policy == 'periodic':
                invoice_ids.append(inv_id)
                str_ = sale_order.client_order_ref or sale_order.name
                str_ += ' Period: '
                str_ += sale_order.invoicing_next_date
                str_ += '-'
                str_ += compute_date(sale_order.invoicing_next_date, sale_order.periodicity)
                invoice_data = {'name': str_, 'date_invoice': sale_order.invoicing_next_date}
                self.pool.get('account.invoice').write(cr, uid, [inv_id], invoice_data)
            new_next_date = compute_date(sale_order.invoicing_next_date, sale_order.periodicity)
            self.write(cr, uid, sale_order.id, {'invoicing_next_date': new_next_date})

        return invoice_ids
sale_order2()
