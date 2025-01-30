# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import api, fields, models, tools
from odoo.exceptions import MissingError, AccessError
from odoo.tools.safe_eval import safe_eval
import json

from ..tools import unquote


class IrActionsActions(models.Model):
    _inherit = 'ir.actions.actions'

    window_action_ids = fields.Many2many(
        'ir.actions.act_window', string="Window Actions",
        compute='_get_window_action_ids', inverse='_set_window_action_ids')
    window_actions = fields.Char('Technical field', readonly=True)

    @api.depends('window_actions')
    def _get_window_action_ids(self):
        ActWindow = self.env['ir.actions.act_window']
        for action in self:
            ids = []
            if action.window_actions:
                ids = list(map(int, filter(
                    bool, action.window_actions.split(','))))
            action.window_action_ids = ActWindow.browse(ids)

    def _set_window_action_ids(self):
        for action in self:
            ids = action.window_action_ids.ids or []
            action.window_actions = ',%s,' % ','.join(map(str, ids))

    @api.model
    @tools.ormcache_context(
        'frozenset(self.env.user.groups_id.ids)', 'model_name',
        keys=('act_window_id',))
    def get_bindings(self, model_name):
        """ Retrieve the list of actions bound to the given model.

           :return: a dict mapping binding types to a list of dict describing
                    actions, where the latter is given by calling the method
                    ``read`` on the action record.
        """
        # DLE P19: Need to flush before doing the SELECT, which act as a search
        # Test `test_bindings`
        self.env.flush_all()
        cr = self.env.cr
        query = """ SELECT a.id, a.type, a.binding_type
                    FROM ir_actions a, ir_model m
                    WHERE a.binding_model_id=m.id AND m.model=%s
                    AND (a.window_actions IS NULL
                         OR a.window_actions like %s)
                    ORDER BY a.id """
        cr.execute(
            query, [model_name,
                    '%%,%s,%%' % self._context.get('act_window_id', '')])

        # discard unauthorized actions, and read action definitions
        result = defaultdict(list)
        user_groups = self.env.user.groups_id
        for action_id, action_model, binding_type in cr.fetchall():
            try:
                action = self.env[action_model].sudo().browse(action_id)
                action_groups = getattr(action, 'groups_id', ())
                if action_groups and not action_groups & user_groups:
                    # the user may not perform this action
                    continue
                result[binding_type].append(action.read()[0])
            except (AccessError, MissingError):
                continue

        return result


class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'

    def _update_context(self):
        eval_dict = {
            'active_id': unquote("active_id"),
            'active_ids': unquote("active_ids"),
            'active_model': unquote("active_model"),
            'uid': unquote("uid"),
            'user': unquote("user"),
            'context': self._context,
        }
        try:
            for act_window in self:
                context = safe_eval(
                    act_window.context or '{}', eval_dict) or {}
                if 'act_window_id' not in context:
                    act_window.context = act_window.context[:1] + \
                        "'act_window_id': %s, " % act_window.id + \
                        act_window.context[1:]
        except Exception:
            pass

    @api.model_create_multi
    def create(self, vals_list):
        act_window = super(IrActionsActWindow, self).create(vals_list)
        act_window._update_context()
        return act_window

    def write(self, vals):
        res = super(IrActionsActWindow, self).write(vals)
        self._update_context()
        return res

    def read(self, fields=None, load='_classic_read'):
        results = super(IrActionsActWindow, self).read(fields, load)
        # Evaluate context value with user
        localdict = {
            'active_model': unquote('active_model'),
            'active_id': unquote('active_id'),
            'active_ids': unquote('active_ids'),
            'uid': unquote('uid'),
            'context': unquote('context'),
            'user': self.env.user,
        }
        for res in results:
            if 'context' in res:
                try:
                    with tools.mute_logger("odoo.tools.safe_eval"):
                        res['context'] = tools.ustr(
                            eval(res['context'], localdict))
                except Exception:
                    continue
        return results


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    # HACK: Overload function to ensure json.load is called with correctly formatted data by relacing single to double quote.
    def _action_configure_external_report_layout(self, report_action):
        action = self.env["ir.actions.actions"]._for_xml_id("web.action_base_document_layout_configurator")
        context = action.get('context', {})
        context = context.replace("'", '"')
        py_ctx = json.loads(context)
        report_action['close_on_report_download'] = True
        py_ctx['report_action'] = report_action
        py_ctx['dialog_size'] = 'large'
        action['context'] = py_ctx
        return action
