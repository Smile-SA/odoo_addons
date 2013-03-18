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

import json
from lxml import etree

from openerp.osv import orm, fields
from openerp.tools.translate import _


class SaleOrderLinksWizard(orm.TransientModel):
    _name = 'sale.order.links_wizard'
    _description = 'Linked Products Wizard'

    _columns = {
        'order_id': fields.many2one('sale.order', 'Sale Order', required=True, ondelete='cascade'),
    }

    def _get_product_price(self, cr, uid, product_link, sale_order, context=None):
        if not product_link.quantity:
            return 0.0
        product = self.pool.get('product.product').browse(cr, uid, product_link.linked_product_id.id, {'pricelist': sale_order.pricelist_id.id,
                                                                                                       'partner': sale_order.partner_id.id,
                                                                                                       'quantity': product_link.quantity})
        return (product_link.price_type == 'standard' and product.price or product_link.special_price) / product_link.quantity

    _dynamic_field = 'product_link_'

    def _get_product_links(self, cr, uid, fields_list=None, context=None):
        if not fields_list:
            return [], fields_list
        link_fields = []
        for field in fields_list[:]:
            if field.startswith(self._dynamic_field):
                link_fields.append(field)
                fields_list.remove(field)
        link_ids = [int(field.replace(self._dynamic_field, '')) for field in link_fields]
        return self.pool.get('product.link').browse(cr, uid, link_ids, context), fields_list

    def default_get(self, cr, uid, fields_list, context=None):
        product_links, fields_list = self._get_product_links(cr, uid, fields_list, context)
        res = super(SaleOrderLinksWizard, self).default_get(cr, uid, fields_list, context)
        for link in product_links:
            res[self._dynamic_field + str(link.id)] = link.mandatory
        return res

    def fields_get(self, cr, uid, fields_list=None, context=None, write_access=True):
        product_links, fields_list = self._get_product_links(cr, uid, fields_list, context)
        res = super(SaleOrderLinksWizard, self).fields_get(cr, uid, fields_list, context, write_access)
        context = context or {}
        order = self.pool.get('sale.order').browse(cr, uid, context.get('default_order_id'), context)
        for link in product_links:
            res[self._dynamic_field + str(link.id)] = {'type': 'boolean',
                                                       'string': _('%s%s - Price: %s') % (link.quantity != 1 and '%s x ' % link.quantity or '',
                                                            link.linked_product_id.name,
                                                            self._get_product_price(cr, uid, link, order, context) * link.quantity),
                                                       'readonly': link.mandatory}
        return res

    _arch = """<form string="Linked Products" version="7.0">
        <group colspan="4" col="2">
        </group>
        <footer>
            <button name="button_validate" class="oe_highlight" string="Validate" type="object"/>
            or
            <button string="Cancel" class="oe_link" special="cancel"/>
        </footer>
    </form>"""

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(SaleOrderLinksWizard, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        context = context or {}
        if view_type == 'form' and context.get('product_link_ids'):
            product_link_fields = [self._dynamic_field + str(link_id) for link_id in context['product_link_ids']]
            res['fields'] = self.fields_get(cr, uid, ['order_id'] + product_link_fields, context)
            main_node = etree.fromstring(self._arch)
            group_node = main_node.find('group')
            for field in product_link_fields:
                modifiers = {"readonly": res['fields'][field]['readonly']}
                group_node.append(etree.Element('field', name=field, modifiers=json.dumps(modifiers)))
            modifiers = {"invisible": True}
            group_node.append(etree.Element('field', name="order_id", modifiers=json.dumps(modifiers)))
            res['arch'] = etree.tostring(main_node)
        return res

    def _add_sale_order_lines(self, cr, uid, vals, context=None):
        order_obj = self.pool.get('sale.order')
        order_line_obj = self.pool.get('sale.order.line')
        product_link_obj = self.pool.get('product.link')
        context = context or {}
        product_link_ids = context['product_link_ids']
        missing_fields = []
        for product_link_id in product_link_ids:
            field_name = self._dynamic_field + str(product_link_id)
            if field_name not in vals:
                missing_fields.append(field_name)
        vals.update(self.default_get(cr, uid, missing_fields, context))
        order = order_obj.browse(cr, uid, vals['order_id'], context)
        for field in vals.keys():
            if field.startswith(self._dynamic_field):
                if vals[field]:
                    link = product_link_obj.browse(cr, uid, int(field.replace(self._dynamic_field, '')), context)
                    line_vals = {
                        'order_id': order.id,
                        'product_id': link.linked_product_id.id,
                        'product_uom_qty': link.quantity,
                    }
                    line_vals.update(order_line_obj.product_id_change(cr, uid, None, order.pricelist_id.id, link.linked_product_id.id,
                                                                      link.quantity, partner_id=order.partner_id.id)['value'])
                    line_vals['price_unit'] = self._get_product_price(cr, uid, link, order, context)
                    order_line_obj.create(cr, uid, line_vals, context)
                del vals[field]
        context['do_not_check_linked_products'] = True
        order_obj.action_button_confirm(cr, uid, [order.id], context)
        return vals

    def create(self, cr, uid, vals, context=None):
        vals = self._add_sale_order_lines(cr, uid, vals, context)
        return super(SaleOrderLinksWizard, self).create(cr, uid, vals, context)

    def button_validate(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}
