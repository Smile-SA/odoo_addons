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

from openerp.osv import orm
from openerp.tools.translate import _


class SaleOrder(orm.Model):
    _inherit = 'sale.order'

    def check_linked_products(self, cr, uid, order_id, context=None):
        product_link_ids = []
        lines = self.browse(cr, uid, order_id, context).order_line
#        products = [line.product_id for line in lines if line.product_id]
        for line in lines:
            if line.product_id and line.product_id.product_link_ids:
                for link in line.product_id.product_link_ids:
#                    if link.linked_product_id not in products:
#                        product_link_ids.append(link.id)
                    product_link_ids.append(link.id)
        if not product_link_ids:
            return True
        context = context or {}
        context['default_order_id'] = order_id
        context['product_link_ids'] = product_link_ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Linked Products'),
            'res_model': 'sale.order.links_wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }

    def action_button_confirm(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        context = context or {}
        if not context.get('do_not_check_linked_products'):
            res = self.check_linked_products(cr, uid, ids[0], context)
            if isinstance(res, dict):
                return res
        return super(SaleOrder, self).action_button_confirm(cr, uid, ids, context)
