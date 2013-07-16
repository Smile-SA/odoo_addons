# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Smile (<http://www.smile.fr>). All Rights Reserved
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


class ResPartner(orm.Model):
    _inherit = 'res.partner'

    def _get_default_company_id(self, cr, uid, context=None):
        return self.pool.get('res.company')._company_default_get(cr, uid, self._name, context=context)

    def _get_default_customer_prefix(self, cr, uid, context=None):
        in_prefix = ''
        company_id = self._get_default_company_id(cr, uid, context)
        if company_id:
            in_prefix = self.pool.get('res.company').browse(cr, uid, company_id, context).in_location_prefix
        return in_prefix

    def _get_default_supplier_prefix(self, cr, uid, context=None):
        out_prefix = ''
        company_id = self._get_default_company_id(cr, uid, context)
        if company_id:
            out_prefix = self.pool.get('res.company').browse(cr, uid, company_id, context).out_location_prefix
        return out_prefix

    def create_stock_location(self, cr, uid, ids, context=None):
        location_obj = self.pool.get('stock.location')
        model_data_obj = self.pool.get('ir.model.data')
        if isinstance(ids, (int, long)):
            ids = [ids]
        customer_is_active = False
        supplier_is_active = False
        in_prefix = self._get_default_customer_prefix(cr, uid, context) or ''
        out_prefix = self._get_default_supplier_prefix(cr, uid, context) or ''
        for partner in self.browse(cr, uid, ids, context):
            if partner.customer:
                customer_is_active = True
            in_vals = {
                'name': in_prefix + partner.name,
                'usage': 'customer',
                'active': customer_is_active,
                'location_id': model_data_obj.get_object_reference(cr, uid, 'stock', 'stock_location_customers')[1],
            }
            customer_location_id = location_obj.create(cr, uid, in_vals, context)
            if partner.supplier:
                supplier_is_active = True
            out_vals = {
                'name': out_prefix + partner.name,
                'usage': 'supplier',
                'active': supplier_is_active,
                'location_id': model_data_obj.get_object_reference(cr, uid, 'stock', 'stock_location_suppliers')[1],
            }
            supplier_location_id = location_obj.create(cr, uid, out_vals, context)
            partner.write({'property_stock_supplier': supplier_location_id, 'property_stock_customer': customer_location_id})
        return True

    def update_stock_location(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        in_prefix = self._get_default_customer_prefix(cr, uid, context) or ''
        out_prefix = self._get_default_supplier_prefix(cr, uid, context) or ''
        for partner in self.browse(cr, uid, ids, context):
            if partner.property_stock_customer:
                partner.property_stock_customer.write({'name': in_prefix + vals['name']})
            if partner.property_stock_supplier:
                partner.property_stock_supplier.write({'name': out_prefix + vals['name']})
        return True

    def update_customer_location(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for partner in self.browse(cr, uid, ids, context):
            if vals.get('customer'):
                partner.property_stock_customer.write({'active': True})
            if not vals.get('customer'):
                partner.property_stock_customer.write({'active': False})
        return True

    def update_supplier_location(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for partner in self.browse(cr, uid, ids, context):
            if vals.get('supplier'):
                partner.property_stock_supplier.write({'active': True})
            if not vals.get('supplier'):
                partner.property_stock_supplier.write({'active': False})
        return True

    def create(self, cr, uid, vals, context=None):
        partner_id = super(ResPartner, self).create(cr, uid, vals, context)
        self.create_stock_location(cr, uid, partner_id, context)
        return partner_id

    def write(self, cr, uid, ids, vals, context=None):
        if 'name' in vals:
            self.update_stock_location(cr, uid, ids, vals, context)
        if 'customer' in vals:
            self.update_customer_location(cr, uid, ids, vals, context)
        if 'supplier' in vals:
            self.update_supplier_location(cr, uid, ids, vals, context)
        return super(ResPartner, self).write(cr, uid, ids, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for partner in self.browse(cr, uid, ids, context):
            if partner.property_stock_customer:
                partner.property_stock_customer.unlink()
            if partner.property_stock_supplier:
                partner.property_stock_supplier.unlink()
        return super(ResPartner, self).unlink(cr, uid, ids, context)
