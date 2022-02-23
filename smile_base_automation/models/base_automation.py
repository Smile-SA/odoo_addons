# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict
import inspect
import logging
import os
import sys

from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.smile_log.tools import SmileDBLogger

_logger = logging.getLogger(__name__)


class BaseAutomationCategory(models.Model):
    _name = 'base.automation.category'
    _description = 'Automated Action Category'

    name = fields.Char(size=64, required=True)


class BaseAutomation(models.Model):
    _inherit = 'base.automation'

    @api.model
    def _setup_fields(self):
        super(BaseAutomation, self)._setup_fields()
        self._fields['last_run'].readonly = False

    category_id = fields.Many2one('base.automation.category', 'Category')
    trigger = fields.Selection(selection_add=[
        ('on_other_method', 'On Other Method')
    ], ondelete={'on_other_method': lambda recs: recs.write(
        {'trigger': 'on_other_method'})})
    method_id = fields.Many2one('ir.model.methods', 'Method',
                                context={'search_default_public': True})
    max_executions = fields.Integer(
        'Max executions', help="Number of time actions are runned")
    force_actions_execution = fields.Boolean(
        'Force actions execution when records list is empty')
    log_ids = fields.One2many('smile.log', 'res_id', 'Logs', readonly=True,
                              domain=[('model_name', '=', 'base.automation')])
    exception_handling = fields.Selection([
        ('continue', 'Ignore actions in exception'),
        ('rollback', 'Rollback transaction'),
    ], 'Exception Handling', required=True, default='rollback')
    exception_warning = fields.Selection([
        ('custom', 'Custom'),
        ('native', 'Native'),
        ('none', 'None'),
    ], 'Exception Warning', required=True, default='native')
    exception_message = fields.Char(
        'Exception Message', size=256, translate=True, required=False)

    @api.onchange('model_id')
    def onchange_model_id(self):
        res = super(BaseAutomation, self).onchange_model_id()
        if self.model_id:
            self.store_model_methods(self.model_id.model)
        return res

    @api.model
    def store_model_methods(self, model_name):
        model = self.env['ir.model'].search(
            [('model', '=', model_name)], limit=1)
        Model = self.env[model.model]
        method_names = []
        for attr in dir(Model):
            try:
                if inspect.ismethod(getattr(Model, attr)):
                    method_names.append(attr)
            except Exception:
                pass
        Method = self.env['ir.model.methods'].sudo()
        existing_method_names = [
            'create', 'write', 'unlink', 'browse', 'exists']
        existing_method_names += [m['name'] for m in Method.search_read([
            ('model_id', '=', model.id),
            ('name', 'in', method_names),
        ], ['name'])]
        for method_name in method_names:
            if method_name in existing_method_names or '__' in method_name:
                continue
            Method.create({'name': method_name, 'model_id': model.id})

    def _filter_pre(self, records):
        return self._filter(records, 'pre')

    def _filter_post(self, records):
        return self._filter(records, 'post')

    def _filter(self, records, filter_type):
        self.ensure_one()
        logger = SmileDBLogger(self._cr.dbname, self._name, self.id, self._uid)
        pid = os.getpid()
        params = [pid, filter_type, self.name,
                  self.model_id.model, tuple(records.ids)]
        try:
            records = getattr(super(BaseAutomation, self),
                              '_filter_%s' % filter_type)(records)
            records = self._filter_max_executions(records)
            logger.debug('[%s] Successful %s-filtering: %s - '
                         'Input records: %s%s - Output records: %s%s'
                         % tuple(params +
                                 [self.model_id.model, tuple(records)]))
            return records
        except Exception as e:
            logger.error('[%s] %s-filtering failed: %s - '
                         'Input records: %s%s - Error: %s'
                         % tuple(params + [repr(e)]))
            if self.exception_handling == 'continue' or \
                    self.exception_warning == 'none':
                return []
            if self.exception_warning == 'custom':
                raise UserError(self.exception_message)
            e.traceback = sys.exc_info()
            raise

    def _filter_max_executions(self, records):
        self.ensure_one()
        if self.max_executions:
            domain = [
                ('rule_id', '=', self.id),
                ('counter', '>=', self.max_executions),
            ]
            records -= self.env['base.automation.execution'].sudo(). \
                search(domain)
        return records

    def _process(self, records, domain_post=None):
        logger = SmileDBLogger(self._cr.dbname, self._name, self.id, self._uid)
        pid = os.getpid()
        params = [pid, self.name, self.model_id.model, tuple(records.ids)]
        logger.debug('[%s] Launching action: %s - Records: %s%s'
                     % tuple(params))
        try:
            # Check if __action_done is in context
            if '__action_done' not in self._context:
                self = self.with_context(__action_done={})
            # Force action execution even if records list is empty
            if not records and self.action_server_id and \
                    self.force_actions_execution:
                ctx = {
                    'active_model': records._name,
                    'active_ids': [],
                    'active_id': False,
                }
                self.action_server_id.with_context(**ctx).run()
                logger.time_info('[%s] Successful action: %s - '
                                 'Records: %s%s' % tuple(params))
            else:
                super(BaseAutomation, self)._process(records, domain_post)
                # Update execution counters
                if self.max_executions:
                    self._update_execution_counter(records)
                if records:
                    logger.time_info('[%s] Successful action: %s - '
                                     'Records: %s%s' % tuple(params))
            return True
        except Exception as e:
            logger.error('[%s] Action failed: %s - '
                         'Records: %s%s - Error: %s'
                         % tuple(params + [repr(e)]))
            if self.exception_handling == 'continue' or \
                    self.exception_warning == 'none':
                return True
            if self.exception_warning == 'custom':
                raise UserError(self.exception_message)
            e.traceback = sys.exc_info()
            raise

    def _update_execution_counter(self, records):
        Execution = self.env['base.automation.execution'].sudo()
        for record in records:
            execution = Execution.search([
                ('rule_id', '=', self.id),
                ('res_id', '=', record.id),
            ], limit=1)
            if execution:
                execution.counter += 1
            else:
                Execution.create({'rule_id': self.id, 'res_id': record.id})
        return True

    def _register_hook(self):
        super(BaseAutomation, self)._register_hook()

        def make_other_method(method_name):
            """ Instanciate an other method for the given automated action. """

            def _other_method(self, *args, **kwargs):
                # retrieve the automated actions to possibly execute
                actions = self.env['base.automation']._get_actions(
                    self, ['on_other_method'])
                actions = actions.filtered(
                    lambda act: act.method_id.name == method_name)
                records = self.with_env(actions.env)
                # check preconditions on records
                pre = {action: action._filter_pre(records)
                       for action in actions}
                # read old values before the update
                old_values = {
                    old_vals.pop('id'): old_vals
                    for pre_records in pre.values()
                    for old_vals in pre_records.read()
                }
                # call original method
                res = _other_method.origin(records, *args, **kwargs)
                # check postconditions, and execute actions
                # on the records that satisfy them
                for action in actions.with_context(old_values=old_values):
                    action._process(action._filter_post(pre[action]))
                return res

            return _other_method

        patched_models = defaultdict(set)

        def patch(model, name, method):
            """ Patch method `name` on `model`,
            unless it has been patched already. """
            if model not in patched_models[name]:
                patched_models[name].add(model)
                model._patch_method(name, method)

        for action_rule in self.with_context({}).search(
                [('trigger', '=', 'on_other_method')]):
            Model = self.env.get(action_rule.model_name)
            # Do not crash if the model of the base_action_rule was uninstalled
            if Model is None:
                _logger.warning("Action rule with ID %d depends on model %s" %
                                (action_rule.id,
                                 action_rule.model_name))
                continue
            name = action_rule.method_id.name
            patch(Model, name, make_other_method(name))


class BaseAutomationExecution(models.Model):
    _name = 'base.automation.execution'
    _description = 'Automated Action Execution'
    _rec_name = 'rule_id'

    rule_id = fields.Many2one(
        'base.automation', 'Automated Action',
        required=False, index=True, ondelete='cascade')
    res_id = fields.Integer('Record', required=False)
    counter = fields.Integer('Executions', default=1)
