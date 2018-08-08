# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class DiscountContractRule(models.Model):
    _name = 'discount.contract.rule'
    _description = 'Discount Contract Rule'

    name = fields.Char(required=True, translate=True)
    contract_tmpl_id = fields.Many2one('discount.contract.template',
                                       'Contract Template',
                                       required=True, ondelete='cascade')
    description = fields.Html(translate=True)
    sequence = fields.Integer(default=10)
    # Filters
    applied_on = fields.Selection([
        ('global', 'Global'),
        ('category', 'Product categories'),
        ('product', 'Products'),
        ('variant', 'Product variants'),
    ], default='global', required=True)
    product_categ_ids = fields.Many2many('product.category',
                                         string='Product categories')
    product_tmpl_ids = fields.Many2many('product.template',
                                        string='Products')
    product_ids = fields.Many2many('product.product',
                                   string='Product variants')
    # Computation criteria
    value_type = fields.Selection([
        ('growth', 'Growth'),
        ('value', 'Value'),
    ], default='value', required=True)
    based_on = fields.Selection([
        ('gross', 'Gross Price'),
        ('net', 'Net Price'),
        ('qty', 'Quantity'),
        ('formula', 'Formula'),
    ], default='net', required=True)
    slice_ids = fields.One2many('discount.contract.rule.slice',
                                'rule_id', 'Discounts by slice', copy=True)
    formula = fields.Text()

    @api.multi
    def write(self, vals):
        self.mapped('contract_tmpl_id')._can_modify()
        return super(DiscountContractRule, self).write(vals)

    @api.multi
    def _compute_base_value(self, invoice_lines):
        self.ensure_one()
        if self.based_on == 'gross':
            total = 0.0
            for line in invoice_lines:
                if line.discount:
                    amount = line.price_unit * line.quantity
                    if line.invoice_id.type in ['in_refund', 'out_refund']:
                        amount *= -1
                    if line.currency_id != line.company_currency_id:
                        amount = line.currency_id.with_context(
                            date=line.invoice_id.date_invoice).compute(
                            amount, line.company_currency_id)
                    total += amount
                else:
                    total += line.price_subtotal_signed
            return total
        elif self.based_on == 'net':
            return sum(invoice_lines.mapped('price_subtotal_signed'))
        elif self.based_on == 'qty':
            return sum(invoice_lines.mapped('quantity'))
        elif self.based_on == 'formula':
            return safe_eval(self.formula, {'rule': self,
                                            'invoice_lines': invoice_lines})

    @api.multi
    def _get_slice_to_apply(self, base_value):
        self.ensure_one()
        slices = self.slice_ids.sorted(key='min_value', reverse=True)
        for slice in slices:
            if base_value >= slice.min_value:
                return slice
        return self.slice_ids.browse()

    @api.multi
    def compute_discount_amount(self, base_value):
        slice = self._get_slice_to_apply(base_value)
        return slice and slice.compute_discount_amount(base_value) or 0.0

    @api.multi
    def get_filters(self):
        self.ensure_one()
        if self.applied_on == 'category' and self.product_categ_ids:
            return [('product_id.categ_id', 'child_of',
                     self.product_categ_ids.ids)]
        elif self.applied_on == 'product' and self.product_tmpl_ids:
            return [('product_id.product_tmpl_id', 'in',
                     self.product_tmpl_ids.ids)]
        elif self.applied_on == 'variant' and self.product_ids:
            return [('product_id', 'in',
                     self.product_ids.ids)]
        return []
