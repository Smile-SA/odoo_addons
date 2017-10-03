# -*- coding: utf-8 -*-

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


class DiscountContractRuleSlice(models.Model):
    _name = 'discount.contract.rule.slice'
    _description = 'Discount Contract Rule Slice'
    _rec_name = 'min_value'
    _order = 'rule_id, min_value'

    rule_id = fields.Many2one('discount.contract.rule', 'Rule',
                              required=True, ondelete='cascade')
    min_value = fields.Float('Min. value', required=True, default=0.0,
                             digits=dp.get_precision('Discount base value'))
    discount_type = fields.Selection([
        ('percent', 'Percentage'),
        ('fixed', 'Fixed price'),
        ('formula', 'Formula'),
    ], default='percent', required=True)
    discount_value = fields.Float('Discount',
                                  digits=dp.get_precision('Discount value'))
    formula = fields.Text()

    @api.onchange('discount_type')
    def _onchange_discount_type(self):
        if self.discount_type == 'formula':
            self.discount_value = 0.0

    @api.multi
    def write(self, vals):
        self.mapped('rule_id.contract_tmpl_id')._can_modify()
        if vals.get('discount_type') == 'formula':
            vals['discount_value'] = 0.0
        return super(DiscountContractRuleSlice, self).write(vals)

    @api.multi
    def compute_discount_amount(self, base_value):
        self.ensure_one()
        if self.discount_type == 'formula':
            return self.formula
        discount_amount = self.discount_value
        if self.discount_type == 'percent':
            discount_amount *= base_value / 100.0
        return discount_amount

    @api.multi
    def edit_formula(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'readonly': True},
        }
