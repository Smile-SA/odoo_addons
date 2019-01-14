# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import api, fields, models, tools
from odoo.exceptions import MissingError, AccessError
from odoo.tools.safe_eval import safe_eval

from ..tools import unquote


class IrActionsActions(models.Model):
    _inherit = 'ir.actions.actions'

    window_action_ids = fields.Many2many(
        'ir.actions.act_window', string="Window Actions",
        compute='_get_window_action_ids', inverse='_set_window_action_ids')
    window_actions = fields.Char('Technical field', readonly=True)

    @api.one
    @api.depends('window_actions')
    def _get_window_action_ids(self):
        ids = None
        if self.window_actions:
            ids = list(map(int, filter(bool, self.window_actions.split(','))))
        self.window_action_ids = self.env['ir.actions.act_window'].browse(ids)

    @api.one
    def _set_window_action_ids(self):
        ids = self.window_action_ids.ids or []
        self.window_actions = ',%s,' % ','.join(map(str, ids))

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
                action = self.env[action_model].browse(action_id)
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

    @api.one
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
            context = safe_eval(self.context or '{}', eval_dict) or {}
            if 'act_window_id' not in context:
                self.context = self.context[:1] + "'act_window_id': %s, " \
                    % self.id + self.context[1:]
        except Exception:
            pass

    @api.model
    def create(self, vals):
        act_window = super(IrActionsActWindow, self).create(vals)
        act_window._update_context()
        return act_window

    @api.multi
    def write(self, vals):
        res = super(IrActionsActWindow, self).write(vals)
        self._update_context()
        return res

    @api.multi
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
