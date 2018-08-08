# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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
                self.context = self.context[:1] + "'act_window_id': %s, " % self.id + self.context[1:]
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
                        res['context'] = tools.ustr(eval(res['context'], localdict))
                except Exception:
                    continue
        return results
