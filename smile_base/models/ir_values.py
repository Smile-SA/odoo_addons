# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp import api, fields, models, _
from openerp.addons.base.ir.ir_values import ACTION_SLOTS, EXCLUDED_FIELDS
from openerp.exceptions import except_orm, Warning
from openerp.tools.safe_eval import safe_eval as eval


class IrValues(models.Model):
    _inherit = 'ir.values'
    _order = 'sequence, id'

    @api.one
    @api.depends('window_action_ids')
    def _get_window_actions(self):
        self.window_actions = ', %s, ' % ', '.join(map(str, self.window_action_ids.ids))

    sequence = fields.Integer('Sequence')
    window_action_ids = fields.Many2many('ir.actions.act_window', 'ir_values_window_actions_rel',
                                         'ir_value_id', 'window_action_id', 'Menus')
    window_actions = fields.Char('Window Actions', size=128, compute='_get_window_actions',
                                 default=', , ', store=True)

    @api.model
    def get_actions(self, action_slot, model, res_id=False):
        assert action_slot in ACTION_SLOTS, 'Illegal action slot value: %s' % action_slot
        # use a direct SQL query for performance reasons,
        # this is called very often
        # Add by Smile #
        cr, uid, context = self.env.args
        query = """SELECT v.id, v.name, v.value FROM ir_values v
                   WHERE v.key = %s AND v.key2 = %s
                        AND v.model = %s
                        AND (v.res_id = %s
                             OR v.res_id IS NULL
                             OR v.res_id = 0)
                         AND (v.window_actions IS NULL
                              OR v.window_actions=', , '
                              OR v.window_actions like %s)
                    ORDER BY v.sequence, v.id"""
        cr.execute(query, ('action', action_slot, model, res_id or None, ', %s, ' % context.get('act_window_id', '')))
        ################
        results = {}
        for action in cr.dictfetchall():
            if not action['value']:
                continue  # skip if undefined
            action_model, action_id = action['value'].split(',')
            if not eval(action_id):
                continue
            fields = [field for field in self.env[action_model]._fields
                      if field not in EXCLUDED_FIELDS]
            # FIXME: needs cleanup
            try:
                action_def = self.env[action_model].browse(int(action_id)).read(fields)
                if isinstance(action_def, list):
                    action_def = action_def[0]
                if action_def:
                    if action_model in ('ir.actions.report.xml', 'ir.actions.act_window',
                                        'ir.actions.wizard'):
                        groups = action_def.get('groups_id')
                        if groups:
                            cr.execute('SELECT 1 FROM res_groups_users_rel WHERE gid IN %s AND uid=%s',
                                       (tuple(groups), uid))
                            if not cr.fetchone():
                                if action['name'] == 'Menuitem':
                                    raise Warning(_('You do not have the permission to perform this operation !!!'))
                                continue
                # keep only the first action registered for each action name
                results[action['name']] = (action['id'], action['name'], action_def)
            except (except_orm, Warning):
                continue
        return sorted(results.values())
