# -*- coding: utf-8 -*-

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


class DiscountContractSubline(models.Model):
    _name = 'discount.contract.subline'
    _description = 'Discount Contrat - Discount by rule and product'
    _rec_name = 'product_id'

    contract_line_id = fields.Many2one('discount.contract.line',
                                       'Contract details', ondelete='cascade',
                                       required=True, readonly=True)
    product_id = fields.Many2one('product.product', 'Product',
                                 required=True, readonly=True)
    base_value = fields.Float(digits=dp.get_precision('Discount base value'),
                              readonly=True)
    discount_amount = fields.Monetary(readonly=True)
    currency_id = fields.Many2one(related='contract_line_id.currency_id',
                                  readonly=True, store=True)
    # Additional fields used in pivot view
    contract_type = fields.Selection(
        related='contract_line_id.contract_id.contract_type',
        store=True, readonly=True)
    date = fields.Date(
        related='contract_line_id.contract_id.date_start',
        store=True, readonly=True)
    partner_id = fields.Many2one(
        related='contract_line_id.contract_id.partner_id',
        store=True, readonly=True)
    product_category_id = fields.Many2one(
        related='product_id.categ_id',
        store=True, readonly=True)
    discount_amount_signed = fields.Monetary(
        compute='_compute_discounts', store=True)
    sale_discount = fields.Monetary(
        compute='_compute_discounts', store=True)
    purchase_discount = fields.Monetary(
        compute='_compute_discounts', store=True)

    @api.one
    @api.depends('discount_amount')
    def _compute_discounts(self):
        self['%s_discount' % self.contract_type] = self.discount_amount
        sign = self.contract_type == 'purchase' and -1 or 1
        self.discount_amount_signed = self.discount_amount * sign
