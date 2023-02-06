# (C) 2023 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import fields, api, models

import logging

_logger = logging.getLogger(__name__)


class IrCronHistory(models.Model):
    _name = 'ir.cron.history'
    _description = 'Scheduled Actions History'
    _order = 'date_start desc'

    ir_actions_server_id = fields.Many2one(
        'ir.actions.server', 'Server action',
        delegate=True, ondelete='cascade', required=True)
    action_name = fields.Char(readonly=True)
    date_start = fields.Datetime(default=lambda self: fields.Datetime.now())
    date_end = fields.Datetime()
    state = fields.Selection([
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('error', 'Error'),
        ('interrupted', 'Interrupted'),
    ], 'Status', default='in_progress', readonly=True)
    message_error = fields.Text()

    @api.model
    def _create_history(self, cron_name, server_action_id):
        # Mark interrupted in progress history
        self.search([
            ('ir_actions_server_id', '=', server_action_id),
            ('state', '=', 'in_progress')
        ]).write({'state': 'interrupted'})
        # Create history
        cron_history = self.sudo().create({
            'ir_actions_server_id': server_action_id,
            'action_name': cron_name
        })
        self._cr.commit()
        return cron_history

    def _done_history(self):
        if self.state == 'in_progress':
            self.sudo().write({
                'state': 'done',
                'date_end': fields.Datetime.now(),
            })

    @api.model
    def _error_history(self, job_exception):
        cron_history_id = self._context.get('cron_history_id')
        if cron_history_id:
            cron_history = self.env['ir.cron.history'].browse(
                cron_history_id).sudo()
            job_error = job_exception.name \
                if hasattr(job_exception, 'name') else job_exception
            cron_history.write({
                'state': 'error',
                'date_end': fields.Datetime.now(),
                'message_error': job_error,
            })

    @api.model
    def cron_cleanup_cron_history(self, days=90):
        _logger.info('Start cleanup cron history')
        limit_date = fields.Date.to_string(
            fields.Date.from_string(fields.Date.today()) -
            relativedelta(days=days))
        cron_history = self.search([('create_date', '<', limit_date)])
        len_histories = len(cron_history.ids)
        _logger.info('History to clean: {}'.format(len_histories))
        cron_history.sudo().unlink()
        _logger.info('End cleanup cron history')
