# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DiscountContractTemplate(models.Model):
    _name = 'discount.contract.template'
    _description = 'Discount Contract Template'
    _inherit = 'mail.thread'

    id = fields.Char(readonly=True)
    name = fields.Char(required=True, translate=True)
    code = fields.Char()
    description = fields.Html(translate=True)
    active = fields.Boolean(default=True)
    contract_type = fields.Selection([
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
    ], required=True, default='sale')
    company_id = fields.Many2one('res.company', 'Company')
    rule_ids = fields.One2many('discount.contract.rule', 'contract_tmpl_id',
                               'Rules', copy=True)
    # Base period
    # TODO: manage prorata temporis and so start month
    months = fields.Integer('Over a period of N-months', required=True,
                            default=12)
    # Refund
    journal_id = fields.Many2one('account.journal', 'Refund journal',
                                 required=True, company_dependent=True)
    product_id = fields.Many2one('product.product', 'Discount product',
                                 required=True, company_dependent=True)
    refund_months = fields.Integer(
        'Refund - Months after the end of contract', default=3)
    refund_day = fields.Integer('Refund - Day of month', default=1)
    # TODO: make refund line name configurable
    contract_ids = fields.One2many('discount.contract', 'contract_tmpl_id',
                                   'Contracts', copy=False)
    nb_of_contracts = fields.Integer(compute='_get_nb_of_contracts')
    parent_id = fields.Many2one('discount.contract.template',
                                'Based on another template',
                                ondelete='restrict')
    child_ids = fields.One2many('discount.contract.template',
                                'parent_id', 'Templates depending on it')
    all_rule_ids = fields.One2many('discount.contract.rule',
                                   string='All rules',
                                   compute='_get_all_rules')

    _sql_constraints = [
        ('check_months', 'CHECK months >= 1',
         'The shortest period is 1 month!'),
    ]

    @api.one
    def _get_nb_of_contracts(self):
        self.nb_of_contracts = len(self.contract_ids)

    @api.one
    def _get_all_rules(self):
        self.all_rule_ids = self.rule_ids | self.parent_id.rule_ids

    @api.onchange('contract_type')
    def _onchange_contract_type(self):
        if self.parent_id and \
                self.parent_id.contract_type != self.contract_type:
            self.parent_id = False

    @api.one
    def name_get(self):
        name = self.name
        if self.code:
            name = '[%s] %s' % (self.code, name)
        return self.id, name

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = [
            '|',
            ('name', operator, name),
            ('code', operator, name),
        ] + (args or [])
        return super(DiscountContractTemplate, self).name_search(
            name, args, operator, limit)

    @api.one
    def _can_modify(self):
        contracts = self.contract_ids | self.child_ids.mapped('contract_ids')
        if contracts.filtered(lambda ctr: ctr.state in ('open', 'close')):
            raise ValidationError(_('You cannot update a template '
                                    'with active contracts'))

    _protected_fields = ['contract_type', 'rule_ids', 'months']

    @api.multi
    def write(self, vals):
        for field in vals:
            if field in self._protected_fields:
                self._can_modify()
                break
        return super(DiscountContractTemplate, self).write(vals)

    @api.multi
    def copy_data(self, default=None):
        self.ensure_one()
        default['name'] = self.name + _(' (copy)')
        return super(DiscountContractTemplate, self).copy_data(default)
