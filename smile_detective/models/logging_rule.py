# -*- coding: utf-8 -*-

from openerp import api, fields, models, SUPERUSER_ID, tools, _


class LoggingRule(models.Model):
    _name = 'ir.logging.rule'
    _description = 'Logging Rule'

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
    log_sql = fields.Boolean('Log SQL queries')

    _sql_constraints = [
        ('check_log_python', "CHECK(log_python IS FALSE OR methods = '' OR methods IS NULL)",
         _('Please to specify methods to profile them'))
    ]

    @tools.ormcache(skiparg=3)
    def _get_logging_rules(self, cr, uid):
        ids = self.search(cr, SUPERUSER_ID, [])
        rules = self.browse(cr, SUPERUSER_ID, ids)
        return [{'user_ids': rule.user_ids.ids,
                 'models': rule.model_ids.mapped('model'),
                 'methods': rule.methods and rule.methods.replace(' ', '').split(',') or [],
                 'log_python': rule.log_python,
                 'log_sql': rule.log_sql}
                for rule in rules]

    def check(self, cr, uid, model, method, log_python=False, log_sql=False):
        for rule in self._get_logging_rules(cr, uid):
            if not rule['user_ids'] or uid in rule['user_ids']:
                if not rule['models'] or model in rule['models']:
                    if not rule['methods'] or method in rule['methods']:
                        if (not log_python or rule['log_python']) and \
                                (not log_sql or rule['log_sql']):
                            return True
        return False

    def clear_cache(self):
        self._get_logging_rules.clear_cache(self)

    @api.model
    def create(self, vals):
        record = super(LoggingRule, self).create(vals)
        self.clear_cache()
        return record

    @api.multi
    def write(self, vals):
        res = super(LoggingRule, self).write(vals)
        self.clear_cache()
        return res

    @api.multi
    def unlink(self):
        res = super(LoggingRule, self).unlink()
        self.clear_cache()
        return res
