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

from openerp import api, models, tools
from openerp.tools.misc import unquote
from openerp.tools.safe_eval import safe_eval as eval
from openerp.addons.base.ir.ir_actions import ir_actions_act_window


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


@api.multi
def read(self, fields=None, load='_classic_read'):
    results = super(ir_actions_act_window, self).read(fields, load)
    localdict = {
        'active_model': unquote('active_model'),
        'active_id': unquote('active_id'),
        'active_ids': unquote('active_ids'),
        'uid': unquote('uid'),
        'user': self.env.user,
    }
    for res in results:
        if 'context' in res:
            res['context'] = eval(res['context'], localdict)
    if not fields or 'help' in fields:
        cr, uid, context = self.env.args
        eval_dict = {
            'active_model': context.get('active_model'),
            'active_id': context.get('active_id'),
            'active_ids': context.get('active_ids'),
            'uid': uid,
        }
        for res in results:
            model = res.get('res_model')
            if model and self.pool.get(model):
                try:
                    with tools.mute_logger("openerp.tools.safe_eval"):
                        eval_context = eval(res['context'] or "{}", eval_dict) or {}
                except Exception:
                    continue
                custom_context = dict(context, **eval_context)
                res['help'] = self.pool[model].get_empty_list_help(cr, uid, res.get('help', ""), context=custom_context)
    return results

ir_actions_act_window.read = read
