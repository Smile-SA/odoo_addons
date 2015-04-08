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

from openerp import api, models, SUPERUSER_ID, tools
from openerp.tools.safe_eval import safe_eval as eval

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
            context = eval(self.context or '{}', eval_dict) or {}
            if 'act_window_id' not in context:
                context['act_window_id'] = self.id
                self.context = tools.ustr(context)
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

    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        ids_int = isinstance(ids, (int, long))
        if ids_int:
            ids = [ids]
        results = super(IrActionsActWindow, self).read(cr, uid, ids, fields, context, load)
        # Evaluate context value with user
        localdict = {
            'active_model': unquote('active_model'),
            'active_id': unquote('active_id'),
            'active_ids': unquote('active_ids'),
            'uid': unquote('uid'),
            'context': unquote('context'),
            'user': self.pool.get('res.users').browse(cr, SUPERUSER_ID, uid, context),
        }
        for res in results:
            if 'context' in res:
                try:
                    with tools.mute_logger("openerp.tools.safe_eval"):
                        res['context'] = tools.ustr(eval(res['context'], localdict))
                except:
                    continue
        return results[0] if ids_int else results
