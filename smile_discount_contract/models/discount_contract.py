# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class DiscountContract(models.Model):
    _name = 'discount.contract'
    _description = 'Discount Contract'
    _inherit = 'mail.thread'
    _order = 'date_start desc'

    @api.model
    def _get_default_company(self):
        return self.env['res.company']._company_default_get(self._name)

    name = fields.Char('Reference', required=True, copy=False, readonly=True,
                       index=True, default=lambda self: _('New'))
    reference = fields.Char('Partner Ref.')
    contract_tmpl_id = fields.Many2one('discount.contract.template',
                                       'Contract template', required=True,
                                       ondelete='restrict')
    contract_type = fields.Selection(related='contract_tmpl_id.contract_type',
                                     readonly=True, store=True)
    company_id = fields.Many2one('res.company', 'Company',
                                 required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 default=_get_default_company)
    currency_id = fields.Many2one(related='company_id.currency_id',
                                  readonly=True, store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('open', 'Validated'),
        ('close', 'Closed'),
        ('cancel', 'Cancelled')
    ], string='Status', required=True, copy=False, default='draft')
    partner_id = fields.Many2one('res.partner', 'Partner',
                                 required=True, ondelete='cascade',
                                 readonly=True,
                                 states={'draft': [('readonly', False)]})
    user_id = fields.Many2one('res.users', 'Contact', required=True,
                              default=lambda self: self.env.user)
    date_start = fields.Date('Start date', readonly=True,
                             states={'draft': [('readonly', False)],
                                     'sent': [('readonly', False)]},
                             default=fields.Date.today)
    date_stop = fields.Date('End date', compute='_get_contract_date_stop',
                            store=True)
    close_reason_id = fields.Many2one('discount.contract.close_reason',
                                      'Close Reason', ondelete='restrict',
                                      states={'close': [('readonly', True)]})
    auto_renew = fields.Boolean('Self-renewal')
    max_renew = fields.Integer('Max renewals', default=-1)
    contract_line_ids = fields.One2many('discount.contract.line',
                                        'contract_id', 'Details',
                                        readonly=True)
    discount_amount = fields.Monetary('Total discount', readonly=True)
    discount_residual = fields.Monetary('Discount to refund', store=True,
                                        compute='_get_discount_residual')
    discount_refund = fields.Monetary('Total refund', store=True,
                                      compute='_get_discount_residual')
    last_update = fields.Datetime(readonly=True)
    refund_ids = fields.One2many('account.invoice', 'discount_contract_id',
                                 'Refunds', readonly=True)
    refund_date = fields.Date('Planned refund date',
                              compute='_get_refund_date', store=True)

    @api.multi
    def _get_contract_timedelta(self):
        self.ensure_one()
        return {'months': self.contract_tmpl_id.months}

    @api.one
    @api.depends('contract_tmpl_id.months', 'date_start')
    def _get_contract_date_stop(self):
        delta = self._get_contract_timedelta()
        date_start = fields.Date.from_string(self.date_start)
        self.date_stop = date_start + \
            relativedelta(**delta) - \
            relativedelta(days=1)

    @api.one
    @api.depends('discount_amount', 'refund_ids.state')
    def _get_discount_residual(self):
        discount_residual = self.discount_amount
        refunds = self.refund_ids.filtered(lambda inv: inv.state != 'cancel')
        if refunds:
            discount_residual += sum(refunds.mapped('amount_untaxed_signed'))
        self.discount_residual = discount_residual
        self.discount_refund = self.discount_amount - self.discount_residual

    @api.one
    @api.depends('contract_tmpl_id.refund_months',
                 'contract_tmpl_id.refund_day',
                 'date_stop')
    def _get_refund_date(self):
        delta = {
            'months': self.contract_tmpl_id.refund_months,
            'day': self.contract_tmpl_id.refund_day,
        }
        self.refund_date = fields.Date.from_string(self.date_stop) + \
            relativedelta(**delta)

    @api.one
    def name_get(self):
        name = self.name
        if self.partner_id:
            name = '%s - %s' % (name, self.partner_id.name)
        if self.contract_tmpl_id.code:
            name = '%s/%s' % (self.contract_tmpl_id.code, name)
        return self.id, name

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq = self.env['ir.sequence']
            if 'company_id' in vals:
                seq = seq.with_context(force_company=vals['company_id'])
            vals['name'] = seq.next_by_code(self._name)
        return super(DiscountContract, self).create(vals)

    @api.multi
    def unlink(self):
        # if any(self.filtered(lambda contract: contract.state
        #                      not in ('draft', 'cancel'))):
        #     raise UserError(_('You cannot delete an active contract!'))
        return super(DiscountContract, self).unlink()

    @api.multi
    def send_by_email(self):
        self.ensure_one()
        template = self.env.ref(
            'smile_discount_contract.email_template_discount_contract')
        compose_form = self.env.ref('mail.email_compose_message_wizard_form')
        ctx = {
            'default_model': self._name,
            'default_res_id': self.id,
            'default_use_template': bool(template),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def force_send_by_email(self):
        for contract in self:
            email_act = contract.send_by_email()
            if email_act and email_act.get('context'):
                email_ctx = email_act['context']
                email_ctx.update(default_email_from=contract.company_id.email)
                contract.with_context(email_ctx).message_post_with_template(
                    email_ctx.get('default_template_id'))
        return True

    @api.multi
    def print_contract(self):
        return self.env['report'].get_action(
            self, 'smile_discount_contract.report_discountcontract')

    @api.multi
    def set_open(self):
        self._create_contract_lines()
        self.write({'state': 'open'})
        if self._context.get('send_email'):
            self.force_send_by_email()
        return True

    @api.multi
    def set_cancel(self):
        return self.write({'state': 'cancel'})

    @api.multi
    def set_close(self):
        if not all(self.mapped('close_reason_id')):
            raise UserError(_('Please specify a close reason'))
        date_stop = fields.Date.today()
        self.write({'state': 'close', 'date_stop': date_stop})
        date_start = fields.Date.from_string(date_stop) + relativedelta(days=1)
        default = {'state': 'open', 'date_start': date_start}
        for contract in self:
            if contract.auto_renew and contract.max_renew:
                default['max_renew'] = contract.max_renew
                contract.copy(default)
        return True

    @api.one
    def _create_contract_lines(self):
        self.contract_line_ids.unlink()
        for rule in self.contract_tmpl_id.all_rule_ids:
            self.contract_line_ids.create({
                'contract_id': self.id,
                'rule_id': rule.id,
            })

    @api.one
    def _compute_discount_amount(self):
        if not self.contract_line_ids:
            self._create_contract_lines()
        self.contract_line_ids._update_contract_line()
        self.discount_amount = sum(self.mapped(
                                   'contract_line_ids.discount_amount'))
        self.last_update = fields.Datetime.now()

    @api.multi
    def compute_discount_amount(self):
        self._compute_discount_amount()
        return True

    @api.multi
    def _get_refund_vals(self):
        self.ensure_one()
        self = self.with_context(force_company=self.company_id.id)
        product = self.contract_tmpl_id.product_id
        name = product.with_context(lang=self.partner_id.lang).display_name
        if self.contract_tmpl_id.contract_type == 'sale':
            invoice_type = 'out_refund'
            account = product.property_account_income_id or \
                product.categ_id.property_account_income_categ_id
            if product.description_sale:
                name += '\n' + product.description_sale
        else:
            invoice_type = 'in_refund'
            account = product.property_account_expense_id or \
                product.categ_id.property_account_expense_categ_id
            if product.description_purchase:
                name += '\n' + product.description_purchase
        fpos = self.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)
        return {
            'type': invoice_type,
            'discount_contract_id': self.id,
            'company_id': self.company_id.id,
            'journal_id': self.contract_tmpl_id.journal_id.id,
            'partner_id': self.partner_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'product_id': product.id,
                'account_id': account.id,
                'price_unit': self.discount_residual,
                'quantity': 1.0,
                'uom_id': product.uom_id.id,
            })],
        }

    @api.multi
    def generate_refund(self):
        for contract in self:
            if contract.discount_residual:
                vals = self._get_refund_vals()
                contract.refund_ids.create(vals)
        return True

    @api.model
    def auto_generate_refund(self):
        # Compute discount amount
        contracts = self.search([
            ('state', 'not in', ('draft', 'cancel')),
        ])
        contracts.compute_discount_amount()
        # Generate refund
        contracts = self.search([
            ('refund_date', '=', fields.Date.today()),
            ('discount_residual', '!=', 0.0),
        ])
        return contracts.generate_refund()

    @api.multi
    def view_refunds(self):
        self.ensure_one()
        if self.contract_tmpl_id.contract_type == 'sale':
            action = self.env.ref('account.action_invoice_tree1').read()[0]
        else:
            action = self.env.ref('account.action_invoice_tree2').read()[0]
        if action.get('domain'):
            eval_context = self.env['ir.actions.actions']._get_eval_context()
            action['domain'] = safe_eval(action['domain'], eval_context)
        else:
            action['domain'] = []
        action['domain'] += [('discount_contract_id', '=', self.id)]
        return action
