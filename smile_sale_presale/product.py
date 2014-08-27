# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>). All Rights Reserved
#                       author cyril.defaria@smile.fr
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
from openerp.osv import (orm, fields)
from openerp.tools.translate import _
from datetime import (datetime, timedelta)
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from time import strptime


class ProductProduct(orm.Model):
    _inherit = 'product.product'
    
    _columns = {
        'release_date': fields.date('Release Date'),
    }


class SaleOrderLine(orm.Model):
    _inherit = "sale.order.line"

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
                            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
                            lang=False, update_tax=True, date_order=False, packaging=False, 
                            fiscal_position=False, flag=False, context=None):
        res = super(SaleOrderLine, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos,
                                                           name=name, partner_id=partner_id, lang=lang, update_tax=update_tax,
                                                           date_order=date_order, packaging=packaging, fiscal_position=fiscal_position,
                                                           flag=flag, context=context)
        if product:
            product_record = self.pool.get('product.product').browse(cr, uid, product, context=context)
            if product_record.release_date:
                release_date_struct_time = strptime(product_record.release_date, DEFAULT_SERVER_DATE_FORMAT)
                release_date = datetime(*release_date_struct_time[:6])
                delta = timedelta(days=product_record.sale_delay)
                delivery_date = (release_date + delta).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                res['value']['delivery_date'] = delivery_date
        return res
