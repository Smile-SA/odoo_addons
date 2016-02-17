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

from openerp import api, fields, models, _
from openerp.exceptions import Warning
import openerp.addons.decimal_precision as dp

import openerp.addons.product.product as native_product


class ProductUomConversion(models.Model):
    _name = 'product.uom.conversion'
    _rec_name = 'uom_name'
    _description = 'Product Unit of Measure Conversion'

    product_tmpl_id = fields.Many2one('product.template', 'Product', required=True, ondelete="cascade")
    uom_id = fields.Many2one('product.uom', 'Unit of Measure', required=True, ondelete="cascade", domain=[('uom_type', '=', 'reference')])
    uom_name = fields.Char('Name', size=64, readonly=True, related='uom_id.name')
    factor = fields.Float('Ratio', digits=(12, 6), required=True, default=1.0)
    factor_revert = fields.Float('Inverse Ratio', digits=(12, 6), required=True, default=1.0)

    @api.one
    @api.constrains('uom_id')
    def _check_data_in_unit_list(self):
        if self.product_tmpl_id.uom_id.category_id == self.uom_id.category_id \
                and self.uom_id == self.product_tmpl_id.uom_id:
            raise Warning(_('Inconsistency of input data is detected, please verify that the category of '
                            'the units of measurement selected does not match the one\'s of the product'))

    _sql_constraints = [
        ('unique_category_conversion', 'UNIQUE(product_tmpl_id, uom_id)', 'Only one conversion by UoM category!'),
        ('positive_factors', 'CHECK(factor>0 AND factor_revert>0)', 'factor and factor_revert  must be positive'),
    ]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    uom_conversion_ids = fields.One2many('product.uom.conversion', 'product_tmpl_id', 'Product Unit of Measure Conversion')

    @api.multi
    def _check_uom(self):
        for product in self:
            if product.uom_po_id.category_id.id not in [product.uom_id.category_id.id] + [conv.uom_id.category_id.id
                                                                                          for conv in product.uom_conversion_ids]:  # Added by Smile
                return False
        return True

    @api.multi
    def write(self, vals):
        if 'uom_po_id' in vals:
            new_uom = self.env['product.uom'].browse(vals['uom_po_id'])
            for product in self:
                old_uom = product.uom_po_id
                if new_uom.category_id.id not in [old_uom.category_id.id] + [conv.uom_id.category_id.id
                                                                             for conv in product.uom_conversion_ids]:  # Added by Smile
                    raise Warning(_("New Unit of Measure '%s' must belong to same Unit of Measure category '%s' as of old Unit "
                                    "of Measure '%s'. If you need to change the unit of measure, you may deactivate this product "
                                    "from the 'Procurements' tab and create a new one.")
                                  % (new_uom.name, old_uom.category_id.name, old_uom.name,))
        if 'standard_price' in vals:
            for product in self:
                product._set_standard_price(vals['standard_price'])
        res = super(native_product.product_template, self).write(vals)
        if 'attribute_line_ids' in vals or vals.get('active'):
            self.create_variant_ids()
        if 'active' in vals and not vals.get('active'):
            product_ids = []
            for product in self.with_context(active_test=False):
                product_ids = map(int, product.product_variant_ids)
            self.env["product.product"].browse(product_ids).write({'active': vals.get('active')})
        return res


class ProductUomCategory(models.Model):
    _inherit = 'product.uom.categ'

    reference_uom_ids = fields.One2many('product.uom', 'category_id', 'Reference Unit Of Measure',
                                        domain=[('uom_type', '=', 'reference')])


class ProductUom(models.Model):
    _inherit = 'product.uom'

    display_precision = fields.Float('Display precision', digits=dp.get_precision('Product Unit of Measure'), default=0.01)

    def _compute_qty(self, cr, uid, from_uom_id, qty, to_uom_id=False, round=True, context=None):
        # Override it just to pass context to _compute_qty_obj
        if not from_uom_id or not qty or not to_uom_id:
            return qty
        uoms = self.browse(cr, uid, [from_uom_id, to_uom_id])
        if uoms[0].id == from_uom_id:
            from_unit, to_unit = uoms[0], uoms[-1]
        else:
            from_unit, to_unit = uoms[-1], uoms[0]
        return self._compute_qty_obj(cr, uid, from_unit, qty, to_unit, round, context)

    def _convert_qty(self, cr, uid, qty, unit, product, is_from_unit=True):
        import operator
        operator_function = is_from_unit and operator.truediv or operator.mul
        if unit != product.uom_id:
            if unit.uom_type != 'reference':
                qty = operator_function(qty, unit.factor)
                unit = unit.category_id.reference_uom_ids[0]
            if unit.category_id != product.uom_id.category_id:
                for unit_conversion in product.uom_conversion_ids:
                    if unit_conversion.uom_id == unit:
                        qty = operator_function(qty, unit_conversion.factor / unit_conversion.factor_revert)
                unit = product.uom_id
        return qty, unit

    def _compute_qty_obj(self, cr, uid, from_unit, qty, to_unit, round=True, rounding_method='UP', context=None):
        if from_unit.category_id.id != to_unit.category_id.id:
            context = context or {}
            product = context.get('uom_product')
            if not product and context.get('uom_product_id'):
                product = self.pool.get('product.product').browse(cr, uid, context['uom_product_id'], context=None)
            if product:
                qty, from_unit = self._convert_qty(cr, uid, qty, from_unit, product, True)
                qty, to_unit = self._convert_qty(cr, uid, qty, to_unit, product, False)
        return super(ProductUom, self)._compute_qty_obj(cr, uid, from_unit, qty, to_unit, round, rounding_method, context)
