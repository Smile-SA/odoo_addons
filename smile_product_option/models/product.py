# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, fields, models
import openerp.addons.decimal_precision as dp

QUANTITY_TYPES = [
    ('free', 'Free'),
    ('fixed', 'Fixed'),
    ('identical', 'Identical to main product'),
    ('free_and_multiple', 'Free and multiple of main product'),
]


class ProductOption(models.Model):
    _name = 'product.option'
    _description = 'Product Option'
    _rec_name = 'optional_product_id'

    @api.model
    def _get_default_uom(self):
        return self.env.ref('product.product_uom_unit', raise_if_not_found=False)

    product_tmpl_id = fields.Many2one('product.template', 'Main Product',
                                      required=True, ondelete="cascade")
    optional_product_id = fields.Many2one('product.product', 'Optional Product',
                                          required=True, ondelete="cascade")
    active = fields.Boolean(related='optional_product_id.active', readonly=True, store=True)
    sequence = fields.Integer('Priority', default=15)
    is_mandatory = fields.Boolean()
    quantity_type = fields.Selection(QUANTITY_TYPES, required=True, default='identical')
    fixed_quantity = fields.Float(digits=dp.get_precision('Product UoS'))
    uom_id = fields.Many2one(related='optional_product_id.uom_id', readonly=True, store=True)

    _sql_constraints = [
        ('check_quantity_type', "CHECK(is_mandatory IS FALSE OR quantity_type <> 'free')",
         'A mandatory option cannot have a free quantity!'),
        ('check_fixed_quantity', "CHECK(quantity_type <> 'fixed' OR fixed_quantity > 0)",
         'Please indicate a fixed quantity!'),
        ('unique_optional_product', "UNIQUE(product_tmpl_id, optional_product_id)",
         'An optional product must appears only once in the options list'),
    ]

    @api.onchange('quantity_type')
    def _onchange_quantity_type(self):
        if self.quantity_type != 'fixed':
            self.fixed_quantity = 0.0


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    option_ids = fields.One2many('product.option', 'product_tmpl_id', 'Options')
