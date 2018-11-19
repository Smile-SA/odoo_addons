# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields, models, tools, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError


class IrLoggingPerfRule(models.Model):
    _name = 'ir.logging.perf.rule'
    _description = 'Perf Logging Rule'

    @api.one
    def _get_users(self):
        self.users = ', '.join(self.user_ids.mapped('name'))

    @api.one
    def _get_models(self):
        self.models = ', '.join(self.model_ids.mapped('model'))

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    user_ids = fields.Many2many('res.users', string='Users')
    users = fields.Char(compute='_get_users')
    model_ids = fields.Many2many('ir.model', string='Models')
    models = fields.Char(compute='_get_models')
    methods = fields.Char()
    log_python = fields.Boolean('Profile Python methods')
    log_sql = fields.Boolean('Log SQL requests')
    path = fields.Char(
        help='Accept regular expression', default='^(?!/longpolling)')
    rpc_min_duration = fields.Float(
        'Slow RPC calls - Min. duration', default=0,
        help='in seconds', digits=dp.get_precision('Logging Time'))
    sql_min_duration = fields.Float(
        'Slow SQL requests - Min. duration', default=0.3,
        help='in seconds', digits=dp.get_precision('Logging Time'))
    recompute_min_duration = fields.Float(
        'Slow fields recomputation - Min. duration', default=0.1,
        help='in seconds', digits=dp.get_precision('Logging Time'))

    @api.one
    @api.constrains('log_python', 'methods')
    def _check_python_logs(self):
        if self.log_python and not self.methods:
            raise ValidationError(
                _('Please to specify methods to profile them'))

    @api.model
    @tools.ormcache()
    def _get_logging_rules(self):
        rules = self.sudo().search([])
        return [{'path': re.compile(rule.path or '.*'),
                 'user_ids': rule.user_ids.ids,
                 'models': rule.model_ids.mapped('model'),
                 'methods': rule.methods and
                 rule.methods.replace(' ', '').split(',') or [],
                 'log_python': rule.log_python,
                 'log_sql': rule.log_sql,
                 'rpc_min_duration': rule.rpc_min_duration,
                 'sql_min_duration': rule.sql_min_duration,
                 'recompute_min_duration': rule.recompute_min_duration}
                for rule in rules]

    @api.model
    def check(self, path, model, method, log_python=False, log_sql=False):
        if model != self._name:
            for rule in self._get_logging_rules():
                if rule['path'].match(path):
                    if not rule['user_ids'] or self._uid in rule['user_ids']:
                        if not rule['models'] or model in rule['models']:
                            if not rule['methods'] or \
                                    method in rule['methods']:
                                if (not log_python or rule['log_python']) and \
                                        (not log_sql or rule['log_sql']):
                                    return True
        return False

    @api.model
    def get_min_duration(self, path, model, method, type='rpc'):
        min_duration = 0.0
        if model != self._name:
            for rule in self._get_logging_rules():
                if rule['path'].match(path):
                    if not rule['user_ids'] or self._uid in rule['user_ids']:
                        if not rule['models'] or model in rule['models']:
                            if not rule['methods'] or \
                                    method in rule['methods']:
                                min_duration_field = '%s_min_duration' % type
                                if rule[min_duration_field]:
                                    if min_duration:
                                        min_duration = min(
                                            min_duration,
                                            rule[min_duration_field])
                                    else:
                                        min_duration = rule[min_duration_field]
        return min_duration

    def clear_cache(self):
        self._get_logging_rules.clear_cache(self)

    @api.model
    def create(self, vals):
        record = super(IrLoggingPerfRule, self).create(vals)
        self.clear_cache()
        return record

    @api.multi
    def write(self, vals):
        res = super(IrLoggingPerfRule, self).write(vals)
        self.clear_cache()
        return res

    @api.multi
    def unlink(self):
        res = super(IrLoggingPerfRule, self).unlink()
        self.clear_cache()
        return res
