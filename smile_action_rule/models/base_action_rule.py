# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import inspect
import os

from openerp import api, fields, models, SUPERUSER_ID, tools

from openerp.addons.smile_log.tools import SmileDBLogger

from action_rule_decorator import action_rule_decorator


class ActionRuleCategory(models.Model):
    _name = 'base.action.rule.category'
    _description = 'Action Rule Category'

    name = fields.Char(size=64, required=True)


class ActionRule(models.Model):
    _inherit = 'base.action.rule'

    def __init__(self, pool, cr):
        super(ActionRule, self).__init__(pool, cr)
        self._columns['kind'].selection = self._get_kinds(cr, SUPERUSER_ID)

    @api.model
    def _get_kinds(self):
        return [
            ('on_create', 'On Creation'),
            ('on_write', 'On Update'),
            ('on_create_or_write', 'On Creation & Update'),
            ('on_unlink', 'On Deletion'),
            ('on_other_method', 'On Other Method'),
            ('on_wkf_activity', 'On Workflow Activity'),
            ('on_time', 'On Timed Condition'),
        ]

    kind = fields.Selection('_get_kinds', 'When to Run', required=True)
    method_id = fields.Many2one('ir.model.methods', 'Method')
    activity_id = fields.Many2one('workflow.activity', 'Activity')
    category_id = fields.Many2one('base.action.rule.category', 'Category')
    max_executions = fields.Integer('Max executions', help="Number of time actions are runned")
    force_actions_execution = fields.Boolean('Force actions execution when resources list is empty')
    log_ids = fields.One2many('smile.log', 'res_id', 'Logs', domain=[('model_name', '=', 'base.action.rule')], readonly=True)
    exception_handling = fields.Selection([
        ('continue', 'Ignore actions in exception'),
        ('rollback', 'Rollback transaction'),
    ], 'Exception Handling', required=True, default='rollback')
    exception_warning = fields.Selection([
        ('custom', 'Custom'),
        ('native', 'Native'),
        ('none', 'None'),
    ], 'Exception Warning', required=True, default='native')
    exception_message = fields.Char('Exception Message', size=256, translate=True, required=True)

    @api.multi
    def _store_model_methods(self, model_id):
        obj = self.env[self.env['ir.model'].sudo().browse(model_id).model]
        method_names = [attr for attr in dir(obj) if inspect.ismethod(getattr(obj, attr))]
        method_obj = self.env['ir.model.methods'].sudo()
        existing_method_names = ['create', 'write', 'unlink']
        existing_method_names += [m['name'] for m in method_obj.search_read([('model_id', '=', model_id),
                                                                             ('name', 'in', method_names)], ['name'])]
        for method_name in method_names:
            if method_name in existing_method_names or method_name.startswith('__'):
                continue
            method = getattr(obj, method_name)
            if hasattr(method, '_api') and '_id' not in str(method._api):
                continue
            method_args = inspect.getargspec(method)[0]
            if not hasattr(method, '_api') and 'ids' not in method_args and 'id' not in method_args:
                continue
            method_obj.create({'name': method_name, 'model_id': model_id})

    def onchange_model_id(self, cr, uid, ids, model_id, context=None):
        res = super(ActionRule, self).onchange_model_id(cr, uid, ids, model_id, context)
        if model_id:
            self.browse(cr, uid, ids, context)._store_model_methods(model_id)
        return res

    def onchange_kind(self, cr, uid, ids, kind, context=None):
        clear_fields = []
        if kind in ['on_create', 'on_create_or_write']:
            clear_fields = ['filter_pre_id', 'trg_date_id', 'trg_date_range', 'trg_date_range_type']
        elif kind in ['on_write', 'on_other_method', 'on_wkf_activity']:
            clear_fields = ['trg_date_id', 'trg_date_range', 'trg_date_range_type']
        elif kind == 'on_time':
            clear_fields = ['filter_pre_id']
        elif kind == 'on_unlink':
            clear_fields = ['filter_id', 'trg_date_id', 'trg_date_range', 'trg_date_range_type']
        return {'value': dict.fromkeys(clear_fields, False)}

    def _filter(self, cr, uid, rule, filter, record_ids, context=None):
        logger = SmileDBLogger(cr.dbname, self._name, rule.id, uid)
        pid = os.getpid()
        try:
            # Allow to compare with other fields of object (in third item of a condition)
            if record_ids and filter and filter.action_rule:
                assert rule.model == filter.model_id, "Filter model different from action rule model"
                model = self.pool[filter.model_id]
                domain = filter._eval_domain(record_ids)
                domain.insert(0, ('id', 'in', record_ids))
                ctx = dict(context or {})
                ctx.update(eval(filter.context))
                res_ids = model.search(cr, uid, domain, context=ctx)
            else:
                res_ids = super(ActionRule, self)._filter(cr, uid, rule, filter, record_ids, context)
            res_ids = rule._filter_max_executions(res_ids)
            logger.debug('[%s] Successful filter: %s,%s - Input records: %s%s - Output records: %s%s'
                         % (pid, rule.name, filter.name, rule.model_id.model, tuple(record_ids),
                            rule.model_id.model, tuple(res_ids)))
            return res_ids
        except Exception, e:
            logger.error('[%s] Filter failed: %s,%s - Input records: %s%s'
                         % (pid, rule.name, filter.name, rule.model_id.model, tuple(record_ids)))
            if rule.exception_handling == 'continue' or rule.exception_warning == 'none':
                return []
            if rule.exception_warning == 'custom':
                raise Warning(rule.exception_message)
            raise e

    def _process(self, cr, uid, rule, record_ids, context=None):
        logger = SmileDBLogger(cr.dbname, self._name, rule.id, uid)
        pid = os.getpid()
        logger.debug('[%s] Launching action: %s - Records: %s%s'
                     % (pid, rule.name, rule.model_id.model, tuple(record_ids)))
        try:
            if context is None:
                context = {}
            # Force action execution even if records list is empty
            if not record_ids and rule.server_action_ids and rule.force_actions_execution:
                action_server_obj = self.pool.get('ir.actions.server')
                ctx = dict(context, active_model=rule.model_id._name, active_ids=[], active_id=False)
                server_action_ids = [act.id for act in rule.server_action_ids]
                action_server_obj.run(cr, uid, server_action_ids, context=ctx)
                logger.time_info('[%s] Successful action: %s - Records: %s%s'
                                 % (pid, rule.name, rule.model_id.model, tuple(record_ids)))
            else:
                super(ActionRule, self)._process(cr, uid, rule, record_ids, context)
                # Update execution counters
                if rule.max_executions:
                    rule._update_execution_counter(record_ids)
            logger.time_info('[%s] Successful action: %s - Records: %s%s'
                             % (pid, rule.name, rule.model_id.model, tuple(record_ids)))
            return True
        except Exception, e:
            logger.error('[%s] Action failed: %s - Records: %s%s - Error: %s'
                         % (pid, rule.name, rule.model_id.model, tuple(record_ids), repr(e)))
            if rule.exception_handling == 'continue' or rule.exception_warning == 'none':
                return True
            if rule.exception_warning == 'custom':
                raise Warning(rule.exception_message)
            raise e

    @api.multi
    def _get_method_names(self):
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        if self.kind in ('on_time', 'on_wkf_activity'):
            return []
        if self.kind == 'on_other_method' and self.method_id:
            return (self.method_id.name,)
        elif self.kind == 'on_create_or_write':
            return ('create', 'write')
        return (self.kind.replace('on_', ''),)

    def _register_hook(self, cr, ids=None):
        # Trigger on any method
        updated = False
        if not ids:
            ids = self.search(cr, SUPERUSER_ID, [])
        for rule in self.browse(cr, SUPERUSER_ID, ids):
            method_names = rule._get_method_names()
            model_obj = self.pool[rule.model_id.model]
            for method_name in method_names:
                method = getattr(model_obj, method_name)
                check = True
                while check:
                    if method.__name__ == 'action_rule_wrapper':
                        break
                    if hasattr(method, 'origin'):
                        method = method.origin
                    else:
                        check = False
                else:
                    decorated_method = action_rule_decorator(getattr(model_obj, method_name))
                    model_obj._patch_method(method_name, decorated_method)
                    updated = True
        if updated:
            self.clear_caches()
        return updated

    @staticmethod
    def _get_method_name(method):
        while True:
            if not hasattr(method, 'origin'):
                break
            method = method.origin
        return method.__name__

    @tools.cache(skiparg=3)
    def _get_action_rules_by_method(self, cr, uid):
        res = {}
        rule_ids = self.search(cr, SUPERUSER_ID, [])
        for rule in self.browse(cr, uid, rule_ids):
            if rule.kind == 'on_time':
                continue
            if rule.kind in ('on_create', 'on_create_or_write'):
                res.setdefault('create', []).append(rule)
            if rule.kind in ('on_write', 'on_create_or_write'):
                res.setdefault('write', []).append(rule)
            elif rule.kind == 'on_unlink':
                res.setdefault('unlink', []).append(rule)
            elif rule.kind == 'on_other_method':
                res.setdefault(rule.method_id.name, []).append(rule)
        return res

    @api.model
    def _get_action_rules(self, method):
        method_name = ActionRule._get_method_name(method)
        return self.sudo()._get_action_rules_by_method().get(method_name, [])

    @tools.cache(skiparg=3)
    def _get_action_rules_by_activity(self, cr, uid):
        res = {}
        rule_ids = self.search(cr, SUPERUSER_ID, [])
        for rule in self.browse(cr, uid, rule_ids):
            if rule.kind == 'on_wkf_activity':
                res.setdefault(rule.activity_id.id, []).append(rule)
        return res

    @api.model
    def _get_action_rules_on_wkf(self, activity_id):
        return self.sudo()._get_action_rules_by_activity().get(activity_id, [])

    @api.one
    def _update_execution_counter(self, res_ids):
        if isinstance(res_ids, (int, long)):
            res_ids = [res_ids]
        exec_obj = self.env['base.action.rule.execution'].sudo()
        for res_id in res_ids:
            execution = exec_obj.search([('rule_id', '=', self.id),
                                         ('res_id', '=', res_id)], limit=1)
            if execution:
                execution.counter += 1
            else:
                exec_obj.create({'rule_id': self.id, 'res_id': res_id})
        return True

    @api.multi
    def _filter_max_executions(self, res_ids):
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        if self.max_executions:
            self._cr.execute("SELECT res_id FROM base_action_rule_execution WHERE rule_id=%s AND counter>=%s",
                             (self.id, self.max_executions))
            res_ids_off = [r[0] for r in self._cr.fetchall()]
            res_ids = list(set(res_ids) - set(res_ids_off))
        return res_ids


class ActionRuleExecution(models.Model):
    _name = 'base.action.rule.execution'
    _description = 'Action Rule Execution'
    _rec_name = 'rule_id'

    rule_id = fields.Many2one('base.action.rule', 'Action rule', required=False, index=True, ondelete='cascade')
    res_id = fields.Integer('Resource', required=False)
    counter = fields.Integer('Executions', default=1)
