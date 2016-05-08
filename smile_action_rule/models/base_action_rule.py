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
import sys

from openerp import api, fields, models, SUPERUSER_ID, tools
from openerp.exceptions import UserError
from openerp.addons.base_action_rule.base_action_rule import DATE_RANGE_FUNCTION, get_datetime

from openerp.addons.smile_log.tools import SmileDBLogger

from ..tools import action_rule_decorator
from copy import deepcopy


class ActionRuleCategory(models.Model):
    _name = 'base.action.rule.category'
    _description = 'Action Rule Category'

    name = fields.Char(size=64, required=True)


class ActionRule(models.Model):
    _inherit = 'base.action.rule'

    @api.model
    def _setup_fields(self, partial):
        super(ActionRule, self)._setup_fields(partial)
        self._fields['last_run'].readonly = False

    kind = fields.Selection(selection_add=[
        ('on_other_method', 'On Other Method'),
        ('on_wkf_activity', 'On Workflow Activity'),
    ], string='When to Run', required=True)
    method_id = fields.Many2one('ir.model.methods', 'Method')
    activity_id = fields.Many2one('workflow.activity', 'Activity')
    category_id = fields.Many2one('base.action.rule.category', 'Category')
    max_executions = fields.Integer('Max executions', help="Number of time actions are runned")
    force_actions_execution = fields.Boolean('Force actions execution when resources list is empty')
    log_ids = fields.One2many('smile.log', 'res_id', 'Logs', readonly=True,
                              domain=[('model_name', '=', 'base.action.rule')])
    exception_handling = fields.Selection([
        ('continue', 'Ignore actions in exception'),
        ('rollback', 'Rollback transaction'),
    ], 'Exception Handling', required=True, default='rollback')
    exception_warning = fields.Selection([
        ('custom', 'Custom'),
        ('native', 'Native'),
        ('none', 'None'),
    ], 'Exception Warning', required=True, default='native')
    exception_message = fields.Char('Exception Message', size=256, translate=True, required=False)
    date_base = fields.Selection([('last_run', 'Last run'), ('date_from', 'Fixed date')], 'Trigger Date Filtered From',
                                 default='last_run')
    trg_date_range_field_id = fields.Many2one('ir.model.fields', string='Delay after trigger date field',
                                              help="If present, will be used instead of Delay after trigger date.",
                                              domain="[('model_id', '=', model_id), ('ttype', '=', 'integer')]")

    @api.multi
    def write(self, vals):
        if 'last_run' in vals:
            if vals.get('date_base') == 'last_run':
                del vals['last_run']
            elif 'date_base' not in vals:
                date_from_rules = self.filtered(lambda r: r.date_base == 'date_from')
                date_from_vals = deepcopy(vals)
                del date_from_vals['last_run']
                if date_from_vals:
                    super(ActionRule, date_from_rules).write(date_from_vals)
                self -= date_from_rules
        if vals:
            return super(ActionRule, self).write(vals)
        return True

    @api.model
    def store_model_methods(self, model_id):
        obj = self.env[self.env['ir.model'].sudo().browse(model_id).model]
        method_names = [attr for attr in dir(obj) if inspect.ismethod(getattr(obj, attr))]
        method_obj = self.env['ir.model.methods'].sudo()
        existing_method_names = ['create', 'write', 'unlink']
        existing_method_names += [m['name'] for m in method_obj.search_read([('model_id', '=', model_id),
                                                                             ('name', 'in', method_names)], ['name'])]
        for method_name in method_names:
            if method_name in existing_method_names or '__' in method_name:
                continue
            method = getattr(obj, method_name)
            if getattr(method, '_api', False):
                api_decorator = method._api.__name__
                if api_decorator not in ('v8', 'multi', 'one') and '_id' not in api_decorator:
                    continue
            method_args = inspect.getargspec(method)[0]
            if not hasattr(method, '_api') and 'ids' not in method_args and 'id' not in method_args:
                continue
            method_obj.create({'name': method_name, 'model_id': model_id})

    def onchange_model_id(self, cr, uid, ids, model_id, context=None):
        res = super(ActionRule, self).onchange_model_id(cr, uid, ids, model_id, context)
        if model_id:
            self.browse(cr, uid, ids, context).store_model_methods(model_id)
        return res

    def _check_delay(self, cr, uid, action, record, record_dt, context=None):
        date_range = record[action.trg_date_range_field_id.name] \
            if action.trg_date_range_field_id else action.trg_date_range
        if action.trg_date_calendar_id and action.trg_date_range_type == 'day':
            start_dt = get_datetime(record_dt)
            action_dt = self.pool['resource.calendar'].schedule_days_get_date(
                cr, uid, action.trg_date_calendar_id.id, date_range,
                day_date=start_dt, compute_leaves=True, context=context
            )
        else:
            delay = DATE_RANGE_FUNCTION[action.trg_date_range_type](date_range)
            action_dt = get_datetime(record_dt) + delay
        return action_dt

    def onchange_kind(self, cr, uid, ids, kind, context=None):
        res = super(ActionRule, self).onchange_kind(cr, uid, ids, kind, context)
        if kind in ['on_create', 'on_create_or_write', 'on_unlink',
                    'on_write', 'on_other_method', 'on_wkf_activity']:
            res['value']['trg_date_range_field_id'] = False
        return res

    @api.multi
    def _filter_pre(self, records):
        self.ensure_one()
        logger = SmileDBLogger(self._cr.dbname, self._name, self.id, self._uid)
        pid = os.getpid()
        params = [pid, self.name, self.model_id.model, tuple(records.ids)]
        try:
            if records and self.filter_pre_id and self.filter_pre_id.action_rule:
                # Allow to compare with other fields of object (in third item of a condition)
                domain = self.filter_pre_id._eval_domain(records)
                domain.insert(0, ('id', 'in', records.ids))
                ctx = dict(self._context or {})
                ctx.update(eval(self.filter_pre_id.context))
                records = records.with_context(**ctx).search(domain)
            else:
                records = super(ActionRule, self)._filter_pre(records)
            records = self._filter_max_executions(records)
            logger.debug('[%s] Successful pre-filter: %s - Input records: %s%s - Output records: %s%s'
                         % tuple(params + [self.model_id.model, tuple(records)]))
            return records
        except Exception, e:
            logger.error('[%s] Pre-filter failed: %s - Input records: %s%s - Error: %s'
                         % tuple(params + [repr(e)]))
            if self.exception_handling == 'continue' or self.exception_warning == 'none':
                return []
            if self.exception_warning == 'custom':
                raise UserError(self.exception_message)
            e.traceback = sys.exc_info()
            raise

    def _filter_post(self, records):
        self.ensure_one()
        logger = SmileDBLogger(self._cr.dbname, self._name, self.id, self._uid)
        pid = os.getpid()
        params = [pid, self.name, self.model_id.model, tuple(records.ids)]
        try:
            if records and self.filter_id and self.filter_id.action_rule:
                # Allow to compare with other fields of object (in third item of a condition)
                domain = self.filter_id._eval_domain(records)
                domain.insert(0, ('id', 'in', records.ids))
                ctx = dict(self._context or {})
                ctx.update(eval(self.filter_id.context))
                records = records.with_context(**ctx).search(domain)
            else:
                records = super(ActionRule, self)._filter_pre(records)
            records = self._filter_max_executions(records)
            logger.debug('[%s] Successful post-filter: %s - Input records: %s%s - Output records: %s%s'
                         % tuple(params + [self.model_id.model, tuple(records)]))
            return records
        except Exception, e:
            logger.error('[%s] Post-filter failed: %s - Input records: %s%s - Error: %s'
                         % tuple(params + [repr(e)]))
            if self.exception_handling == 'continue' or self.exception_warning == 'none':
                return []
            if self.exception_warning == 'custom':
                raise UserError(self.exception_message)
            e.traceback = sys.exc_info()
            raise

    @api.multi
    def _process(self, records):
        self.ensure_one()
        logger = SmileDBLogger(self._cr.dbname, self._name, self.id, self._uid)
        pid = os.getpid()
        params = [pid, self.name, self.model_id.model, tuple(records.ids)]
        logger.debug('[%s] Launching action: %s - Records: %s%s' % tuple(params))
        try:
            # Check if __action_done is in context
            if '__action_done' not in self._context:
                self = self.with_context(__action_done={})
            # Force action execution even if records list is empty
            if not records and self.server_action_ids and self.force_actions_execution:
                ctx = {'active_model': records._name, 'active_ids': [], 'active_id': False}
                self.server_action_ids.with_context(**ctx).run()
                logger.time_info('[%s] Successful action: %s - Records: %s%s' % tuple(params))
            else:
                super(ActionRule, self)._process(records)
                # Update execution counters
                if self.max_executions:
                    self._update_execution_counter(records)
            logger.time_info('[%s] Successful action: %s - Records: %s%s' % tuple(params))
            return True
        except Exception, e:
            logger.error('[%s] Action failed: %s - Records: %s%s - Error: %s' % tuple(params + [repr(e)]))
            if self.exception_handling == 'continue' or self.exception_warning == 'none':
                return True
            if self.exception_warning == 'custom':
                raise UserError(self.exception_message)
            e.traceback = sys.exc_info()
            raise

    @api.multi
    def _get_method_names(self):
        self.ensure_one()
        if self.kind in ('on_time', 'on_wkf_activity'):
            return tuple()
        if self.kind == 'on_change':
            return 'onchange',
        if self.kind == 'on_other_method' and self.method_id:
            return self.method_id.name,
        elif self.kind == 'on_create_or_write':
            return 'create', 'write'
        return self.kind.replace('on_', ''),

    def _register_hook(self, cr, ids=None):

        def make_onchange(action_rule_id):
            """ Instanciate an onchange method for the given action rule. """
            def base_action_rule_onchange(self):
                action_rule = self.env['base.action.rule'].browse(action_rule_id)
                server_actions = action_rule.server_action_ids.with_context(active_model=self._name, onchange_self=self)
                result = {}
                for server_action in server_actions:
                    res = server_action.run()
                    if res and 'value' in res:
                        res['value'].pop('id', None)
                        self.update(self._convert_to_cache(res['value'], validate=False))
                    if res and 'domain' in res:
                        result.setdefault('domain', {}).update(res['domain'])
                    if res and 'warning' in res:
                        result['warning'] = res['warning']
                return result
            return base_action_rule_onchange

        updated = False
        if not ids:
            ids = self.search(cr, SUPERUSER_ID, [])
        for rule in self.browse(cr, SUPERUSER_ID, ids):
            model_obj = self.pool[rule.model_id.model]
            if rule.kind == 'on_change':
                # Trigger on change
                method = make_onchange(rule.id)
                for field_name in rule.on_change_fields.split(","):
                    field_name = field_name.strip()
                    model_obj._onchange_methods[field_name].append(method)
            else:
                # Trigger on any method
                method_names = rule._get_method_names()
                for method_name in method_names:
                    method = getattr(model_obj, method_name)
                    if method.__name__ != 'action_rule_wrapper':
                        model_obj._patch_method(method_name, action_rule_decorator())
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
            res.setdefault(rule.model, {})
            if rule.kind in ('on_create', 'on_create_or_write'):
                res[rule.model].setdefault('create', []).append(rule.id)
            if rule.kind in ('on_write', 'on_create_or_write'):
                res[rule.model].setdefault('write', []).append(rule.id)
            elif rule.kind == 'on_unlink':
                res[rule.model].setdefault('unlink', []).append(rule.id)
            elif rule.kind == 'on_other_method':
                res[rule.model].setdefault(rule.method_id.name, []).append(rule.id)
        return res

    @api.model
    def _get_action_rules(self, model, method):
        method_name = ActionRule._get_method_name(method)
        return self.sudo()._get_action_rules_by_method().get(model, {}).get(method_name, [])

    @tools.cache(skiparg=3)
    def _get_action_rules_by_activity(self, cr, uid):
        res = {}
        rule_ids = self.search(cr, SUPERUSER_ID, [])
        for rule in self.browse(cr, uid, rule_ids):
            if rule.kind == 'on_wkf_activity':
                res.setdefault(rule.activity_id.id, []).append(rule.id)
        return res

    @api.model
    def _get_action_rules_on_wkf(self, activity_id):
        return self.sudo()._get_action_rules_by_activity().get(activity_id, [])

    @api.one
    def _update_execution_counter(self, records):
        exec_obj = self.env['base.action.rule.execution'].sudo()
        for record in records:
            execution = exec_obj.search([('rule_id', '=', self.id),
                                         ('res_id', '=', record.id)], limit=1)
            if execution:
                execution.counter += 1
            else:
                exec_obj.create({'rule_id': self.id, 'res_id': record.id})
        return True

    @api.multi
    def _filter_max_executions(self, records):
        self.ensure_one()
        if self.max_executions:
            domain = [('rule_id', '=', self.id), ('counter', '>=', self.max_executions)]
            records -= self.env['base.action.rule.execution'].sudo().search(domain)
        return records


class ActionRuleExecution(models.Model):
    _name = 'base.action.rule.execution'
    _description = 'Action Rule Execution'
    _rec_name = 'rule_id'

    rule_id = fields.Many2one('base.action.rule', 'Action rule', required=False, index=True, ondelete='cascade')
    res_id = fields.Integer('Resource', required=False)
    counter = fields.Integer('Executions', default=1)
