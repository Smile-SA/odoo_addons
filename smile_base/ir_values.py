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

import logging

from openerp.addons.base.ir.ir_values import ACTION_SLOTS, EXCLUDED_FIELDS
from openerp.osv import fields, orm
from openerp.tools.misc import unquote
from openerp.tools.safe_eval import safe_eval as eval


class IrValues(orm.Model):
    _inherit = 'ir.values'
    _order = 'sequence, id'

    def _get_visibility_options(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        for value in self.read(cr, uid, ids, ['window_action_ids'], context):
            res[value['id']] = ', %s, ' % ', '.join(map(str, value['window_action_ids']))
        return res

    _columns = {
        'sequence': fields.integer('Sequence'),
        'window_action_ids': fields.many2many('ir.actions.act_window', 'ir_values_window_actions_rel', 'ir_value_id', 'window_action_id', 'Menus'),
        'window_actions': fields.function(_get_visibility_options, method=True, type='char', size=128, string='Window Actions', store={
            'ir.values': (lambda self, cr, uid, ids, context=None: ids, None, 10),
        }),
    }

    _defaults = {
        'window_actions': ', , '
    }

    def get_actions(self, cr, uid, action_slot, model, res_id=False, context=None):
        """Retrieves the list of actions bound to the given model's action slot.
           See the class description for more details about the various action
           slots: :class:`~.ir_values`.

           :param string action_slot: the action slot to which the actions should be
                                      bound to - one of ``client_action_multi``,
                                      ``client_print_multi``, ``client_action_relate``,
                                      ``tree_but_open``.
           :param string model: model name
           :param int res_id: optional record id - will bind the action only to a
                              specific record of the model, not all records.
           :return: list of action tuples of the form ``(id, name, action_def)``,
                    where ``id`` is the ID of the default entry, ``name`` is the
                    action label, and ``action_def`` is a dict containing the
                    action definition as obtained by calling
                    :meth:`~openerp.osv.osv.osv.read` on the action record.
        """
        assert action_slot in ACTION_SLOTS, 'Illegal action slot value: %s' % action_slot
        # use a direct SQL query for performance reasons,
        # this is called very often
        # Add by Smile #
        context = context or {}
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
        cr.execute(query, ('action', action_slot, model, res_id or None, ', %s, ' % context.get('window_action_id', '')))
        ################
        results = {}
        for action in cr.dictfetchall():
            if not action['value']:
                continue    # skip if undefined
            action_model, id = action['value'].split(',')
            fields = [field for field in self.pool.get(action_model)._all_columns
                      if field not in EXCLUDED_FIELDS]
            # FIXME: needs cleanup
            try:
                action_def = self.pool.get(action_model).read(cr, uid, int(id), fields, context)
                if action_def:
                    if action_model in ('ir.actions.report.xml', 'ir.actions.act_window',
                                        'ir.actions.wizard'):
                        groups = action_def.get('groups_id')
                        if groups:
                            cr.execute('SELECT 1 FROM res_groups_users_rel WHERE gid IN %s AND uid=%s',
                                       (tuple(groups), uid))
                            if not cr.fetchone():
                                if action['name'] == 'Menuitem':
                                    raise orm.except_orm('Error !',
                                                         'You do not have the permission to perform this operation !!!')
                                continue
                # keep only the first action registered for each action name
                # Add by Smile #
                if action_slot == 'tree_but_open' and action_def['type'] == 'ir.actions.act_window':
                    try:
                        action_context = eval(action_def['context'], {'active_id': unquote("active_id"), 'uid': uid})
                        action_context['window_action_id'] = action_def['id']
                        action_def['context'] = unicode(action_context)
                    except Exception as e:
                        logging.getLogger('smile.base').warning('Error in eval: %s - %s' % (action_def['context'], repr(e)))
                ################
                results[action['name']] = (action['id'], action['name'], action_def)
            except orm.except_orm:
                continue
        return sorted(results.values())
