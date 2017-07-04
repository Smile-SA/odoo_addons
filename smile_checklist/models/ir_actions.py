# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.tools.misc import unquote
from odoo.tools.safe_eval import safe_eval as eval


class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'

    @api.one
    def _update_context(self):
        eval_dict = {
            'active_id': unquote("active_id"),
            'active_ids': unquote("active_ids"),
            'active_model': unquote("active_model"),
            'uid': self._uid,
            'context': self._context,
        }
        try:
            context = eval(self.context or '{}', eval_dict) or {}
            if 'act_window_id' not in context:
                context['act_window_id'] = self.id
                self.context = '%s' % context
        except:
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
