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


class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        result = super(IrActionsActWindow, self).read(fields, load=load)
        if len(self.ids) == 1:
            res = isinstance(result, list) and result[0] or result
            context = dict(self._context)
            eval_dict = {
                'active_model': context.get('active_model'),
                'active_id': context.get('active_id'),
                'active_ids': context.get('active_ids'),
                'uid': self._uid,
                'context': context,
            }
            try:
                with tools.mute_logger("openerp.tools.safe_eval"):
                    eval_context = eval(res.get('context') or "{}", eval_dict) or {}
                    eval_context['act_window_id'] = self.ids[0]
                    res['context'] = str(eval_context)
            except:
                pass
        return result
