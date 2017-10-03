# -*- coding: utf-8 -*-

from odoo import api, fields, models


class DiscountContractLine(models.Model):
    _inherit = 'discount.contract.line'

    contract_subline_ids = fields.One2many('discount.contract.subline',
                                           'contract_line_id',
                                           'Contract details by product')
    next_slice_id = fields.Many2one('discount.contract.rule.slice',
                                    'Next slice', compute='_get_next_slice')

    @api.one
    @api.depends('base_value')
    def _get_next_slice(self):
        current_slice = self.rule_id._get_slice_to_apply(self.base_value)
        for slice in self.rule_id.slice_ids.sorted(key='min_value'):
            if slice.min_value > current_slice.min_value:
                self.next_slice_id = slice
                break

    @api.model
    def create(self, vals):
        record = super(DiscountContractLine, self).create(vals)
        record._create_contract_sublines()
        return record

    @api.one
    def _create_contract_sublines(self):
        invoice_lines = self._get_invoice_lines()
        for product in invoice_lines.mapped('product_id'):
            self.env['discount.contract.subline'].create({
                'contract_line_id': self.id,
                'product_id': product.id,
            })

    @api.one
    def _update_contract_line(self):
        super(DiscountContractLine, self)._update_contract_line()
        self._update_contract_sublines()

    @api.one
    def _update_contract_sublines(self):
        if not self.contract_subline_ids:
            self._create_contract_sublines()
        slice = self.rule_id._get_slice_to_apply(self.base_value)
        invoice_lines = self._get_invoice_lines()
        for subline in self.contract_subline_ids:
            prod_inv_lines = invoice_lines.filtered(
                lambda invl: invl.product_id == subline.product_id)
            subline.base_value = self.rule_id._compute_base_value(
                prod_inv_lines)
            if slice:
                discount_amount = slice.compute_discount_amount(
                    subline.base_value)
                if slice.discount_type == 'fixed':
                    discount_amount *= subline.base_value / self.base_value
                subline.discount_amount = discount_amount
