# -*- coding: utf-8 -*-
# (C) 2025 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models, _
from odoo.exceptions import UserError


class ScriptIntervention(models.Model):
    _name = 'smile.script.intervention'
    _description = 'Maintenance Intervention'
    _rec_name = 'create_date'
    _order = 'create_date DESC'

    script_id = fields.Many2one(
        'smile.script', 'Script', required=True, readonly=True)
    create_date = fields.Datetime(
        'Start date', required=True, readonly=True,
        default=fields.Datetime.now)
    end_date = fields.Datetime('End date', readonly=True)
    create_uid = fields.Many2one(
        'res.users', 'User', required=True, readonly=True)
    state = fields.Selection([
        ('running', 'Running'),
        ('done', 'Done'),
        ('exception', 'Exception'),
    ], readonly=True, required=True, default='running')
    test_mode = fields.Boolean('Test Mode', readonly=True)
    result = fields.Text(readonly=True)
    log_ids = fields.One2many(
        'smile.log', 'res_id', 'Logs', readonly=True,
        domain=[('model_name', '=', 'smile.script.intervention')])

    def unlink(self):
        if not all(self.mapped('test_mode')):
            raise UserError(_('Intervention cannot be deleted'))
        return super().unlink()
