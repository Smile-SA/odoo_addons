# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import psycopg2

from odoo import fields, models, SUPERUSER_ID
from odoo.exceptions import UserError

LOG_LEVELS = [
    ('0', 'NOTSET'),
    ('10', 'DEBUG'),
    ('20', 'INFO'),
    ('30', 'WARNING'),
    ('40', 'ERROR'),
    ('50', 'CRITICAL'),
]


class IrModelImpexTemplate(models.AbstractModel):
    _name = 'ir.model.impex.template'
    _description = 'Import/Export Template'

    name = fields.Char(size=64, required=True)
    model_id = fields.Many2one(
        'ir.model', 'Model', required=True, ondelete='cascade')
    method = fields.Char(
        size=64, required=True,
        help='Arguments can be passed through Method args '
             'or received at import/export creation call')
    method_args = fields.Char(
        help="Arguments passed as a dictionary\nExample: {'code': '705000'}")
    cron_id = fields.Many2one('ir.cron', 'Scheduled Action', copy=False)
    server_action_id = fields.Many2one(
        'ir.actions.server', 'Server action', copy=False)
    new_thread = fields.Boolean()
    log_level = fields.Selection(LOG_LEVELS, default='20', required=True)
    log_entry_args = fields.Boolean('Log entry arguments', default=True)
    log_returns = fields.Boolean('Log returns')
    one_at_a_time = fields.Boolean()

    def _try_lock(self, warning=None):
        self = self.filtered(lambda tmpl: tmpl.one_at_a_time)
        if not self:
            return
        try:
            self._cr.execute("""SELECT id FROM "%s" WHERE id IN %%s
            FOR UPDATE NOWAIT""" % self._table, (
                tuple(self.ids),), log_exceptions=False)
        except psycopg2.OperationalError:
            # INFO: Early rollback to allow translations
            # to work for the user feedback
            self._cr.rollback()
            if warning:
                raise UserError(warning)
            raise

    def _get_cron_vals(self, **kwargs):
        vals = {
            'user_id': SUPERUSER_ID,
            'ir_actions_server_id': self.server_action_id.id,
            'numbercall': -1,
        }
        vals.update(kwargs)
        return vals

    def create_cron(self, **kwargs):
        self.ensure_one()
        self.create_server_action()
        if not self.cron_id:
            vals = self._get_cron_vals(**kwargs)
            cron_id = self.env['ir.cron'].create(vals)
            self.write({'cron_id': cron_id.id})
        return True

    def _get_server_action_vals(self, **kwargs):
        model = self.env['ir.model'].search(
            [('model', '=', self._name)], limit=1)
        vals = {
            'name': self.name,
            'model_id': model.id,
            'state': 'code',
        }
        vals.update(kwargs)
        return vals

    def create_server_action(self, **kwargs):
        self.ensure_one()
        if not self.server_action_id:
            vals = self._get_server_action_vals(**kwargs)
            self.server_action_id = self.env['ir.actions.server'].create(vals)
        return True

    def unlink_server_action(self):
        self.ensure_one()
        if self.server_action_id:
            self.server_action_id.unlink()
        return True
