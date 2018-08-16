# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models, registry, SUPERUSER_ID, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    execution_mode = fields.Selection([
        ('sync', 'Synchronous'),
        ('async', 'Asynchronous'),
    ], required=True, default='sync')
    cron_id = fields.Many2one(
        'ir.cron', 'Scheduled Action', readonly=True)

    @api.model
    def create(self, vals):
        report = super(IrActionsReport, self).create(vals)
        report._update_cron()
        return report

    @api.multi
    def write(self, vals):
        res = super(IrActionsReport, self).write(vals)
        self._update_cron()
        return res

    @api.one
    def _update_cron(self):
        if self.execution_mode != 'async' and self.cron_id:
            self.cron_id.unlink()
        if self.execution_mode == 'async' and not self.cron_id:
            vals = self._get_cron_vals()
            self.cron_id = self.env['ir.cron'].create(vals)

    @api.multi
    def _get_cron_vals(self):
        self.ensure_one()
        return {
            "name": "Printing %s" % self.name,
            "model_id": self.env.ref(
                "smile_asynchronous_report.model_ir_actions_report_execution"
            ).id,
            "state": "code",
            "code": "model.auto_print_report()",
            "user_id": SUPERUSER_ID,
            "active": True,
            "interval_number": 1,
            "interval_type": "minutes",
            "numbercall": -1,
            "doall": False,
            "priority": 15,
        }

    @api.multi
    def render_qweb_pdf(self, res_ids=None, data=None):
        if not self._context.get('force_render_qweb_pdf'):
            content = self.render_in_asynchronous_mode(res_ids, data)
            if content:
                return content, 'pdf'
        return super(IrActionsReport, self).render_qweb_pdf(res_ids, data)

    @api.multi
    def render_in_asynchronous_mode(self, res_ids, data):
        self.ensure_one()
        if self.execution_mode == 'async':
            with registry(self._cr.dbname).cursor() as new_cr:
                self = self.with_env(self.env(cr=new_cr))
                self._check_execution(res_ids, data)
            raise UserError(_('Printing in progress. '
                              'You will be notified as soon as done.'))

    @api.one
    def _check_execution(self, res_ids, data):
        arguments = repr((res_ids, data))
        context = repr(self._context)
        execution = self.env['ir.actions.report.execution'].search([
            ('report_id', '=', self.id),
            ('arguments', '=', arguments),
            ('context', '=', context),
            ('state', '!=', 'done'),
        ], limit=1)
        if execution:
            execution.user_ids |= self.env.user
        else:
            execution.create({
                'report_id': self.id,
                'arguments': arguments,
                'context': context,
            })
