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

import time

from openerp import api, models, fields

from ..tools import unquote


class ActionFilter(models.Model):
    _inherit = 'ir.filters'

    @api.one
    @api.depends('domain')
    def _get_action_rule(self):
        localdict = {'object': unquote('object'), 'time': time,
                     'active_id': unquote("active_id"), 'uid': self._uid}
        eval_domain = eval(self.domain.replace(' ', ''), localdict)
        self.action_rule = ',object.' in eval_domain

    action_rule = fields.Boolean('Only for action rules', compute='_get_action_rule', store=True)

    def get_filters(self, cr, uid, model, action_id=None):
        action_domain = self._get_action_domain(cr, uid, action_id)
        filter_ids = self.search(cr, uid, action_domain + [
            ('model_id', '=', model),
            ('user_id', 'in', (uid, False)),
            ('action_rule', '=', False),
        ])
        my_filters = self.read(cr, uid, filter_ids, ['name', 'is_default', 'domain', 'context', 'user_id'])
        return my_filters

    @api.multi
    def _eval_domain(self, record_ids=None):
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        domain = []
        eval_domain = eval(self.domain, {'object': unquote('object')})
        for cond in eval_domain:
            if isinstance(cond, tuple) and 'object' in cond[2]:
                subdomain = []
                records = self.env[self.model_id.model].browse(record_ids)
                for record in records:
                    new_cond = (cond[0], cond[1], eval(cond[2], {'object': record}))
                    subdomain.append(new_cond)
                subdomain = list(set(subdomain))
                subdomain = ['|'] * (len(subdomain) - 1) + subdomain
                domain.extend(subdomain)
            else:
                domain.append(cond)
        return domain
