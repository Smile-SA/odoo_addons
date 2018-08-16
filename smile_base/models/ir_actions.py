# -*- coding: utf-8 -*-
# (C) 2010 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, tools
from odoo.tools.safe_eval import safe_eval

from ..tools import unquote


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
