# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountExportTemplate(models.Model):
    _name = 'account.export.template'
    _description = 'Account Export Template'
    _inherit = ['mail.thread']

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    create_uid = fields.Many2one('res.users', 'Created by', readonly=True)
    provider = fields.Selection([], 'Provider', required=True)
    company_id = fields.Many2one(
        'res.company', "Company", required=True, ondelete='restrict',
        default=lambda self: self._get_default_company())
    journal_ids = fields.Many2many(
        'account.journal', string='Account Journals')
    account_ids = fields.Many2many(
        'account.account', string='Accounts')
    force_export = fields.Boolean(
        'Force export', default=False,
        help="Moves lines already exported will be exported again")
    export_ids = fields.One2many(
        'account.export', 'export_tmpl_id', 'Exports',
        readonly=True, copy=False)
    exports_count = fields.Integer(
        'Number of exports', compute='_get_count_exports')
    has_non_draft_exports = fields.Boolean(
        'Has non-draft export(s)', compute='_get_count_exports')
    cron_id = fields.Many2one('ir.cron', 'Scheduled action', copy=False)

    @api.model
    def _get_default_company(self):
        return self.env['res.company']._company_default_get(self._name)

    @api.one
    @api.depends('export_ids')
    def _get_count_exports(self):
        self.exports_count = len(self.export_ids)
        self.has_non_draft_exports = bool(self.export_ids.filtered(
            lambda exp: exp.state != 'draft'))

    @api.multi
    def create_export(self, vals=None):
        self.ensure_one()
        vals = vals or {}
        vals['export_tmpl_id'] = self.id
        export = self.env['account.export'].create(vals)
        export.run_export()
        return True

    @api.multi
    def create_cron(self):
        self.ensure_one()
        if not self.cron_id:
            vals = self._get_cron_vals()
            self.cron_id = self.cron_id.sudo().create(vals)
        return {
            'name': _('Scheduled Action'),
            'type': 'ir.actions.act_window',
            'res_model': self.cron_id._name,
            'view_mode': 'form',
            'view_id': False,
            'res_id': self.cron_id.id,
            'target': 'new',
        }

    @api.multi
    def _get_cron_vals(self):
        self.ensure_one()
        return {
            'name': self.name,
            'interval_number': 7,
            'interval_type': 'days',
            'numbercall': -1,
            'doall': False,
            'model': self._name,
            'function': 'create_export',
            'args': repr([[self.id]]),
        }

    @api.multi
    def write(self, vals):
        self._check_update(vals)
        return super(AccountExportTemplate, self).write(vals)

    _unwritable_fields = ['provider', 'company_id', 'journal_ids',
                          'account_ids', 'force_export']

    @api.multi
    def _check_update(self, vals):
        for field in vals:
            if field in self._unwritable_fields:
                if any(self.mapped('has_non_draft_exports')):
                    raise UserError(_('You cannot modify a template '
                                      'which has a non-draft export.'))
                break
