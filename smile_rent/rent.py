# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Pathé (<http://www.pathe.fr>). All Rights Reserved
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

from openerp import netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import orm, fields
from openerp.tools.translate import _

STATES = [
    ('draft', 'Draft'),
    ('confirmed', 'Confirmed'),
    ('in_progress', 'In progress'),
    ('done', 'Done'),
    ('cancel', 'Canceled'),
]


class RentalOrder(orm.Model):
    _name = 'rental.order'
    _description = 'Rental Order'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _track = {
        'state': {
            'smile_rent.mt_rental_confirmed': lambda self, cr, uid, obj, context=None: obj['state'] == 'confirmed',
            'smile_rent.mt_rental_in_progress': lambda self, cr, uid, obj, context=None: obj['state'] == 'in_progress',
            'smile_rent.mt_rental_done': lambda self, cr, uid, obj, context=None: obj['state'] == 'done',
            'smile_rent.mt_rental_cancel': lambda self, cr, uid, obj, context=None: obj['state'] == 'cancel',
        },
    }

    def _get_out_date_effective(self, cr, uid, ids, name, arg, context=None):
        res = {}.fromkeys(ids, False)
        cr.execute("SELECT order_id, min(out_date_effective) FROM rental_order_line "
                   "WHERE order_id IN %s AND out_date_effective IS NOT NULL GROUP BY order_id", (tuple(ids),))
        res.update(dict((row[0], row[1]) for row in cr.fetchall()))
        return res

    def _get_in_date_effective(self, cr, uid, ids, name, arg, context=None):
        res = {}.fromkeys(ids, False)
        cr.execute("SELECT order_id FROM rental_order_line "
                   "WHERE order_id IN %s AND in_date_effective IS NULL GROUP BY order_id", (tuple(ids),))
        order_ids_to_check = set(ids) - set(row[0] for row in cr.fetchall())
        cr.execute("SELECT order_id, max(in_date_effective) FROM rental_order_line "
                   "WHERE order_id IN %s AND in_date_effective IS NOT NULL GROUP BY order_id", (tuple(order_ids_to_check),))
        res.update(dict((row[0], row[1]) for row in cr.fetchall()))
        return res

    def _get_rental_order_ids_from_pickings(self, cr, uid, ids, picking_type, context=None):
        assert picking_type in ('out', 'in'), "picking_type must be 'in' or 'out'"
        cr.execute("SELECT order_id FROM rental_order_line WHERE " + picking_type + "_picking_id IN %s", (tuple(ids),))
        return list(set(cr.fetchall()))

    def _get_rental_order_ids_from_out_pickings(self, cr, uid, ids, context=None):
        return self.pool.get('rental.order')._get_rental_order_ids_from_pickings(cr, uid, ids, 'out', context)

    def _get_rental_order_ids_from_in_pickings(self, cr, uid, ids, context=None):
        return self.pool.get('rental.order')._get_rental_order_ids_from_pickings(cr, uid, ids, 'in', context)

    _columns = {
        'name': fields.char('Reference', size=64, readonly=True),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True, states={'draft': [('readonly', False)]},
                                      domain=['|', ('customer', '=', True), ('supplier', '=', True)],
                                      required=True, ondelete='restrict'),
        'partner_shipping_out_id': fields.many2one('res.partner', 'Delivery Address', required=False,
                                                   readonly=True, states={'draft': [('readonly', False)]}),
        'partner_shipping_in_id': fields.many2one('res.partner', 'Incoming Shipment Address', required=False,
                                                   readonly=True, states={'draft': [('readonly', False)]}),

        'state': fields.selection(STATES, 'State', required=True),

        'company_id': fields.many2one('res.company', 'Company', required=True),
        'user_id': fields.many2one('res.users', 'Salesperson', readonly=True),

        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', required=False),
        'location_id': fields.many2one('stock.location', 'Delivery Location', required=False),
        'location_dest_id': fields.many2one('stock.location', 'Incoming Shipment Location', required=False),

        'line_ids': fields.one2many('rental.order.line', 'order_id', 'Order Lines', readonly=True, states={'draft': [('readonly', False)]}),

        'out_date_expected': fields.datetime('Requested Delivery Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'in_date_expected': fields.datetime('Requested Incoming Shipment Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),

        'confirm_date': fields.datetime('Validation Date', readonly=True),

        'out_date_effective': fields.function(_get_out_date_effective, method=True, type='datetime', store={
            'stock.picking': (_get_rental_order_ids_from_out_pickings, ['date_done'], 20),
        }, string='Effective Delivery Date'),
        'in_date_effective': fields.function(_get_in_date_effective, method=True, type='datetime', store={
            'stock.picking': (_get_rental_order_ids_from_in_pickings, ['date_done'], 20),
        }, string='Effective Delivery Date'),
    }

    _order = "out_date_expected desc"

    def _get_default_company_id(self, cr, uid, context=None):
        return self.pool.get('res.company')._company_default_get(cr, uid, self._name, context=context)

    def _get_warehouse_id_from_company(self, cr, uid, company_id, context=None):
        warehouse_ids = self.pool.get('stock.warehouse').search(cr, uid, [('company_id', '=', company_id)], limit=1, context=context)
        return warehouse_ids and warehouse_ids[0] or False

    def _get_default_warehouse_id(self, cr, uid, context=None):
        company_id = self._get_default_company_id(cr, uid, context)
        return self._get_warehouse_id_from_company(cr, uid, company_id, context)

    def _get_location_id_from_warehouse(self, cr, uid, warehouse_id, location_type='output', context=None):
        assert location_type in ('input', 'stock', 'output'), "location_type must be 'input', 'stock' or 'output'"
        field = 'lot_%s_id' % location_type
        return self.pool.get('stock.warehouse').read(cr, uid, warehouse_id, [field], context, '_classic_write')[field]

    def _get_default_location_id(self, cr, uid, context=None):
        warehouse_id = self._get_default_warehouse_id(cr, uid, context)
        return self._get_location_id_from_warehouse(cr, uid, warehouse_id, 'output', context)

    def _get_default_location_dest_id(self, cr, uid, context=None):
        warehouse_id = self._get_default_warehouse_id(cr, uid, context)
        return self._get_location_id_from_warehouse(cr, uid, warehouse_id, 'input', context)

    _defaults = {
        'name': '/',
        'state': 'draft',
        'company_id': _get_default_company_id,
        'user_id': lambda self, cr, uid, context=None: uid,
        'warehouse_id': _get_default_warehouse_id,
        'location_id': _get_default_location_id,
        'location_dest_id': _get_default_location_dest_id,
        'out_date_expected': lambda *a: time.strftime('%Y-%m-%d 00:00:00'),
    }

    def _check_dates(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for order in self.read(cr, uid, ids, ['out_date_expected', 'in_date_expected'], context):
            if order['out_date_expected'] > order['in_date_expected']:
                return False
        return True

    _constraints = [
        (_check_dates, 'Delivery date must be before return date', ['out_date_expected', 'in_date_expected']),
    ]

    _sql_constraints = [
        ('uniq_name', 'UNIQUE(name)', 'Reference must be unique'),
    ]

    def create(self, cr, uid, vals, context=None):
        vals['name'] = self.pool.get('ir.sequence').get(cr, uid, self._name)
        return super(RentalOrder, self).create(cr, uid, vals, context)

    def _get_default_values(self, cr, uid, default=None, context=None):
        default = default or {}
        default.update({
            'name': '/',
            'state': 'draft',
            'user_id': uid,
            'confirm_date': False,
            'out_date_effective': False,
            'in_date_effective': False,
        })
        return default

    def copy_data(self, cr, uid, order_id, default=None, context=None):
        default = self._get_default_values(cr, uid, default, context)
        return super(RentalOrder, self).copy_data(cr, uid, order_id, default, context)

    def _create_pickings_and_procurements(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context):
            for line in order.line_ids:
                line._create_pickings_and_procurement()
        return True

    def _get_pickings_to_cancel(self, cr, orders, context=None):
        picking_ids = []
        for order in orders:
            for line in order.line_ids:
                if line.out_picking_id:
                    if line.out_picking_id.state not in ('done', 'cancel'):
                        picking_ids.extend([line.out_picking_id.id, line.in_picking_id.id])
                    elif line.in_picking_id and line.in_picking_id.state != 'cancel' and line.out_picking_id.state == 'cancel':
                        picking_ids.append(line.in_picking_id.id)
        return picking_ids

    def _cancel_pickings(self, cr, uid, orders, context=None):
        wf_service = netsvc.LocalService('workflow')
        for picking_id in self._get_pickings_to_cancel(cr, orders, context):
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_cancel', cr)

    def _get_procurements_to_cancel(self, cr, orders, context=None):
        procurement_ids = []
        for order in orders:
            for line in order.line_ids:
                if line.procurement_id and line.procurement_id.state not in ('done', 'cancel'):
                    procurement_ids.append(line.procurement_id.id)
        return procurement_ids

    def _cancel_procurements(self, cr, uid, orders, context=None):
        wf_service = netsvc.LocalService('workflow')
        for procurement_id in self._get_procurements_to_cancel(cr, orders, context):
            wf_service.trg_validate(uid, 'procurement.order', procurement_id, 'button_cancel', cr)

    def _cancel_pickings_and_procurements(self, cr, uid, ids, context=None):
        orders = self.browse(cr, uid, ids, context)
        self._cancel_pickings(cr, uid, orders, context)
        self._cancel_procurements(cr, uid, orders, context)
        line_ids = [line.id for order in orders for line in order.line_ids]
        return self.pool.get('rental.order.line').write(cr, uid, line_ids, {
            'out_picking_id': False,
            'in_picking_id': False,
            'procurement_id': False,
        }, context)

    def onchange_warehouse_id(self, cr, uid, ids, warehouse_id, context=None):
        location_id = False
        location_dest_id = False
        if warehouse_id:
            location_id = self._get_location_id_from_warehouse(cr, uid, warehouse_id, 'output', context)
            location_dest_id = self._get_location_id_from_warehouse(cr, uid, warehouse_id, 'input', context)
        return {'value': {'location_id': location_id, 'location_dest_id': location_dest_id}}

    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        res = {'value': {'warehouse_id': False, 'location_id': False, 'location_dest_id': False}}
        if company_id:
            warehouse_id = self._get_warehouse_id_from_company(cr, uid, company_id, context)
            res = self.onchange_warehouse_id(cr, uid, ids, warehouse_id, context)
            res['value']['warehouse_id'] = warehouse_id
        return res

    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        res = {'value': {'partner_shipping_out_id': False, 'partner_shipping_in_id': False}}
        if partner_id:
            partner_shipping_id = self.pool.get('res.partner').address_get(cr, uid, [partner_id], ['delivery'])['delivery']
            res['value']['partner_shipping_out_id'] = partner_shipping_id
            res['value']['partner_shipping_in_id'] = partner_shipping_id
        return res

    def _check_rental_order_at_confirmation(self, cr, uid, order, context=None):
        if not order.line_ids:
            raise orm.except_orm(_('Error!'), _('You cannot confirm a rental order which has no line.'))

    def button_confirm(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService('workflow')
        for order in self.browse(cr, uid, ids, context):
            self._check_rental_order_at_confirmation(cr, uid, order, context)
            wf_service.trg_validate(uid, self._name, order.id, 'button_confirm', cr)
        return True

    def action_set_to_draft(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'draft'}, context)

    def action_confirm(self, cr, uid, ids, context=None):
        self._create_pickings_and_procurements(cr, uid, ids, context=None)
        return self.write(cr, uid, ids, {'state': 'confirmed'}, context)

    def action_make_in_progress(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'in_progress'}, context)

    def action_close(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'done'}, context)

    def action_cancel(self, cr, uid, ids, context=None):
        self._cancel_pickings_and_procurements(cr, uid, ids, context=None)
        return self.write(cr, uid, ids, {'state': 'cancel'}, context)

    def get_rental_order_from_stock_picking(self, cr, uid, ids, picking_type, context=None):
        assert picking_type in ('out', 'in'), "picking_type must be 'in' or 'out'"
        res = []
        picking_field = '%s_picking_id' % picking_type
        for order in self.browse(cr, uid, ids, context):
            for line in order.line_ids:
                picking_id = getattr(line, picking_field).id
                if picking_id:
                    res.append(picking_id)
        return res

    def test_pickings(self, cr, uid, ids, picking_type, context=None):
        assert picking_type in ('out', 'in'), "picking_type must be 'in' or 'out'"
        for order in self.browse(cr, uid, ids, context):
            for line in order.line_ids:
                if picking_type == 'out':
                    if line.out_picking_id and line.out_picking_id.state == 'done':
                        return True
                if picking_type == 'in':
                    if not line.in_picking_id or line.in_picking_id.state != 'done':
                        return False
        return picking_type == 'in'

    def _needaction_domain_get(self, cr, uid, context=None):
        if self._needaction:
            return [('state', '=', 'draft'), ('user_id', '=', uid)]
        return []


class RentalOrderLine(orm.Model):
    _name = "rental.order.line"
    _description = "Rental Order Line"

    def _get_rental_order_line_ids_from_pickings(self, cr, uid, ids, picking_type, context=None):
        assert picking_type in ('out', 'in'), "picking_type must be 'in' or 'out'"
        if isinstance(ids, (int, long)):
            ids = [ids]
        return self.pool.get('rental.order.line').search(cr, uid, [('%s_picking_id' % picking_type, 'in', ids)], context=context)

    def _get_rental_order_line_ids_from_out_pickings(self, cr, uid, ids, context=None):
        return self.pool.get('rental.order.line')._get_rental_order_line_ids_from_pickings(cr, uid, ids, 'out', context)

    def _get_rental_order_line_ids_from_in_pickings(self, cr, uid, ids, context=None):
        return self.pool.get('rental.order.line')._get_rental_order_line_ids_from_pickings(cr, uid, ids, 'in', context)

    _columns = {
        'order_id': fields.many2one('rental.order', 'Rental Order', required=True, select=True, ondelete='cascade'),
        'product_id': fields.many2one('product.product', 'Product', domain=[('rental', '=', True)], required=True),
        'packaging_id': fields.many2one('product.packaging', 'Packaging'),  # TODO: manage me in form view
        'name': fields.char('Description', size=128, required=True),
        'qty': fields.float('Quantity', digits_compute=dp.get_precision('Product UoS'), required=True),
        'uom_id': fields.many2one('product.uom', 'Unit Of Measure', required=True),
        'uos_qty': fields.float('Quantity (UoS)', digits_compute=dp.get_precision('Product UoS'), required=True),
        'uos_id': fields.many2one('product.uom', 'Unit Of Stock', required=True),

        'location_id': fields.many2one('stock.location', 'Delivery Location', required=True),
        'location_dest_id': fields.many2one('stock.location', 'Incoming Shipment Location', required=True),

        'out_date_expected': fields.datetime('Requested Delivery Date', required=True),
        'in_date_expected': fields.datetime('Requested Incoming Shipment Date', required=True),

        'out_picking_id': fields.many2one('stock.picking.out', 'Delivery Order', readonly=True),
        'in_picking_id': fields.many2one('stock.picking.in', 'Incoming Shipment', readonly=True),

        'out_date_effective': fields.related('out_picking_id', 'date_done', type='datetime', store={
            'stock.picking': (_get_rental_order_line_ids_from_out_pickings, ['date_done'], 10),
        }, string='Effective Delivery Date', readonly=True),
        'in_date_effective': fields.related('in_picking_id', 'date_done', type='datetime', store={
            'stock.picking': (_get_rental_order_line_ids_from_in_pickings, ['date_done'], 10),
        }, string='Effective Incoming Shipment Date', readonly=True),

        'procurement_id': fields.many2one('procurement.order', 'Procurement Order', readonly=True),

        'partner_shipping_out_id': fields.many2one('res.partner', 'Delivery Address', required=True),
        'partner_shipping_in_id': fields.many2one('res.partner', 'Incoming Shipment Address', required=True),
    }

    _defaults = {
        'qty': 1.0,
        'uos_qty': 1.0,
    }

    def _check_dates_by_line(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.browse(cr, uid, ids, context):
            if line.out_date_expected > line.in_date_expected:
                return False
        return True

    def _check_dates_compared_with_order(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.browse(cr, uid, ids, context):
            order = line.order_id
            for field in ('out_date_expected', 'in_date_expected'):
                if not (order.out_date_expected <= getattr(line, field) <= order.in_date_expected):
                    return False
        return True

    def _check_uom(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.browse(cr, uid, ids, context):
            if line.product_id.uom_id.category_id != line.uom_id.category_id:
                return False
        return True

    def _check_uos(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.browse(cr, uid, ids, context):
            if not line.product_id.uos_id:
                return not line.product_id.uos_id
            elif line.product_id.uos_id.category_id != line.uos_id.category_id:
                return False
        return True

    _constraints = [
        (_check_dates_by_line, 'Delivery date must be before return date', ['out_date_expected', 'in_date_expected']),
        (_check_dates_compared_with_order, 'Dates in line must be in rental order period', ['out_date_expected', 'in_date_expected']),
        (_check_uom, 'Invalid Unit of Measure', ['uom_id']),
        (_check_uos, 'Invalid Unit of Stock', ['uos_id']),
    ]

    def _get_default_values(self, cr, uid, default=None, context=None):
        default = default or {}
        default.update({
            'out_picking_id': False,
            'in_picking_id': False,
            'out_date_effective': False,
            'in_date_effective': False,
            'procurement_id': False,
        })
        return default

    def copy_data(self, cr, uid, line_id, default=None, context=None):
        self._get_default_values(cr, uid, default, context)
        return super(RentalOrderLine, self).copy_data(cr, uid, line_id, default, context)

    def onchange_product_id(self, cr, uid, ids, product_id, qty, uom_id, uos_qty, uos_id, field, context=None):
        # TODO: manage field argument
        if not product_id:
            return {'value': {'uos_qty': qty, 'uos_id': uom_id}}
        values = {}
        product = self.pool.get('product.product').browse(cr, uid, product_id, context)
        if field == 'product_id':
            values['name'] = product.name
        if not uom_id:
            values['uom_id'] = product.uom_id.id
            if uos_id:
                qty = product.uos_coeff and uos_qty / product.uos_coeff or 0.0
                values['qty'] = qty
        if not uos_id:
            values['uos_id'] = product.uos_id.id or product.uom_id.id
        values['uos_qty'] = qty * product.uos_coeff if product.uos_id else qty
        return {'value': values}

    def _get_move_vals(self, cr, uid, line, picking_type, context=None):
        assert picking_type in ('out', 'in'), "picking_type must be 'in' or 'out'"
        date_planned = getattr(line, '%s_date_expected' % picking_type)
        partner_location_id = line.order_id.partner_id.property_stock_customer.id
        if line.order_id.partner_id.supplier:
            partner_location_id = line.order_id.partner_id.property_stock_supplier.id
        return {
            'name': line.name,
            'product_id': line.product_id.id,
            'date': date_planned,
            'date_expected': date_planned,
            'product_qty': line.qty,
            'product_uom': line.uom_id.id,
            'product_uos_qty': line.uos_qty if line.uos_id else line.qty,
            'product_uos': line.uos_id.id or line.uom_id.id,
            'product_packaging': line.packaging_id.id,
            'partner_id': getattr(line, 'partner_shipping_%s_id' % picking_type).id,
            'location_id': line.location_id.id if picking_type == 'out' else partner_location_id,
            'location_dest_id': line.location_dest_id.id if picking_type == 'in' else partner_location_id,
            'tracking_id': False,
            'state': 'draft',
            'company_id': line.order_id.company_id.id,
        }

    def _get_picking_vals(self, cr, uid, line, picking_type, context=None):
        assert picking_type in ('out', 'in'), "picking_type must be 'in' or 'out'"
        return {
            'name': self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.%s' % picking_type),
            'origin': line.order_id.name,
            'date': getattr(line, '%s_date_expected' % picking_type),
            'type': picking_type,
            'state': 'draft',
            'move_type': 'one',
            'partner_id': getattr(line, 'partner_shipping_%s_id' % picking_type).id,
            'note': line.name,
            'invoice_state': 'none',
            'company_id': line.order_id.company_id.id,
        }

    def _get_procurement_vals(self, cr, uid, line, picking_id, context=None):
        return {
            'name': line.name,
            'origin': line.order_id.name,
            'date_planned': line.out_date_expected,
            'product_id': line.product_id.id,
            'product_qty': line.qty,
            'product_uom': line.uom_id.id,
            'product_uos_qty': line.uos_qty if line.uos_id else line.qty,
            'product_uos': line.uos_id.id if line.uos_id else line.uom_id.id,
            'location_id': line.location_id.id,
            'procure_method': line.product_id.procure_method,
            'move_id': False,
            'company_id': line.order_id.company_id.id,
            'note': line.name,
        }

    def _get_grouped_picking_key(self, cr, uid, line, picking_type, context=None):
        assert picking_type in ('out', 'in'), "picking_type must be 'in' or 'out'"
        location_field = picking_type == 'out' and 'location_id' or 'location_dest_id'
        expected_date_field = '%s_date_expected' % picking_type
        shipping_address_field = 'partner_shipping_%s_id' % picking_type
        return (
            line.order_id.id,
            getattr(line, location_field).id,
            getattr(line, shipping_address_field),
            getattr(line, expected_date_field)
        )

    def _get_grouped_picking_ids_by_order(self, cr, uid, orders, picking_type, context=None):
        picking_field = '%s_picking_id' % picking_type
        grouped_pickings = {}
        for order in orders:
            for line in order.line_ids:
                picking = getattr(line, picking_field)
                if picking and picking.state not in ('done', 'cancel'):
                    grouped_pickings[self._get_grouped_picking_key(cr, uid, line, picking_type, context)] = picking.id
        return grouped_pickings

    def _create_picking(self, cr, uid, line, picking_type, grouped_pickings, context=None):
        assert picking_type in ('out', 'in'), "picking_type must be 'in' or 'out'"
        picking_obj = self.pool.get('stock.picking.%s' % picking_type)
        grouped_picking_key = self._get_grouped_picking_key(cr, uid, line, picking_type, context)
        if grouped_picking_key in grouped_pickings:
            picking_id = grouped_pickings[grouped_picking_key]
        else:
            picking_vals = self._get_picking_vals(cr, uid, line, picking_type, context)
            picking_id = picking_obj.create(cr, uid, picking_vals, context)
            grouped_pickings[grouped_picking_key] = picking_id
        move_vals = self._get_move_vals(cr, uid, line, picking_type, context=None)
        picking_obj.write(cr, uid, picking_id, {'move_lines': [(0, 0, move_vals)]}, context)
        netsvc.LocalService("workflow").trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
        return picking_id

    def _create_procurement(self, cr, uid, line, context=None):
        procurement_vals = self._get_procurement_vals(cr, uid, line, context)
        procurement_id = self.pool.get('procurement.order').create(cr, uid, procurement_vals, context)
        netsvc.LocalService("workflow").trg_validate(uid, 'procurement.order', procurement_id, 'button_confirm', cr)
        return procurement_id

    def _create_pickings_and_procurement(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        lines = self.browse(cr, uid, ids, context)
        orders = [line.order_id for line in lines]
        grouped_pickings_out = self._get_grouped_picking_ids_by_order(cr, uid, orders, 'out', context)
        grouped_pickings_in = self._get_grouped_picking_ids_by_order(cr, uid, orders, 'in', context)
        for line in lines:
            vals = {}
            if not line.out_picking_id:
                vals['out_picking_id'] = self._create_picking(cr, uid, line, 'out', grouped_pickings_out, context)
            if not line.in_picking_id:
                vals['in_picking_id'] = self._create_picking(cr, uid, line, 'in', grouped_pickings_in, context)
            if not line.procurement_id:
                vals['procurement_id'] = self._create_procurement(cr, uid, line, context)
            if vals:
                line.write(vals)
        return True
