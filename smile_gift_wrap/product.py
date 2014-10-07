# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>). All Rights Reserved
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
from openerp.tools.translate import _


class ProductProduct(orm.Model):
    _inherit = "product.product"
    _columns = {
        'is_gift_ok': fields.boolean('Is a gift wrap?'),
        'can_be_wrapped_gift_ok': fields.boolean(_('Can be wrapped ?'))
        }

    def _check_gift(self, cr, uid, ids, context=None):
        for product in self.browse(cr, uid, ids, context=context):
            if product.type != 'service' and product.is_gift_ok:
                return False
        return True

    _constraints = [
        (_check_gift, 'The gift wrap product must be a service',
            ['is_gift_ok', 'type'])]
