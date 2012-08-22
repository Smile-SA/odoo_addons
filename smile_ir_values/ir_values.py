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

from osv import fields, osv
from osv.orm import except_orm
import pickle

EXCLUDED_FIELDS = set((
    'report_sxw_content', 'report_rml_content', 'report_sxw', 'report_rml',
    'report_sxw_content_data', 'report_rml_content_data', 'search_view',))


class IrValues(osv.osv):
    _inherit = 'ir.values'

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

    _order = 'sequence, id'

    def get(self, cr, uid, key, key2, models, meta=False, context={}, res_id_req=False, without_user=True, key2_req=True):
        # Add by Smile
        context = context or {}
        window_action_id = ''
        if context.get('active_model') == 'ir.ui.menu':
            action = self.pool.get('ir.ui.menu').read(cr, uid, context.get('active_id', False), ['action'], context)['action']
            if action and action.startswith('ir.actions.act_window, '):
                window_action_id = action.replace('ir.actions.act_window, ', '')
        #####
        result = []
        for m in models:
            if isinstance(m, (list, tuple)):
                m, res_id = m
            else:
                res_id = False

            where = ['key=%s', 'model=%s']
            params = [key, str(m)]
            if key2:
                where.append('key2=%s')
                params.append(key2[: 200])
            elif key2_req and not meta:
                where.append('key2 is null')
            if res_id_req and (models[-1][0] == m):
                if res_id:
                    where.append('res_id=%s')
                    params.append(res_id)
                else:
                    where.append('(res_id is NULL)')
            elif res_id:
                if (models[-1][0] == m):
                    where.append('(res_id=%s or (res_id is null))')
                    params.append(res_id)
                else:
                    where.append('res_id=%s')
                    params.append(res_id)
            # Add by Smile to manage visibility in function of window actions
            if window_action_id:
                where.append("(window_actions=', , ' or window_actions like '%%%%, %s, %%%%')" % window_action_id)
            # Add by Smile to manage sequence
            where.append('(user_id=%s or (user_id IS NULL)) order by ' + self._order)
            #####
            params.append(uid)
            clause = ' and '.join(where)
            cr.execute('select id, name, value, object, meta, key from ir_values where ' + clause, tuple(params))
            result = cr.fetchall()
            if result:
                break

        if not result:
            return []

        def _result_get(x, keys):
            if x[1] in keys:
                return False
            keys.append(x[1])
            if x[3]:
                model, id = x[2].split(',')
                # FIXME: It might be a good idea to opt-in that kind of stuff
                # FIXME: instead of arbitrarily removing random fields
                fields = [
                    field
                    for field in self.pool.get(model).fields_get_keys(cr, uid)
                    if field not in EXCLUDED_FIELDS]

                try:
                    datas = self.pool.get(model).read(cr, uid, [int(id)], fields, context)
                except except_orm:
                    return False
                datas = datas and datas[0]
                if not datas:
                    return False
            else:
                datas = pickle.loads(x[2].encode('utf-8'))
            if meta:
                return (x[0], x[1], datas, pickle.loads(x[4]))
            return (x[0], x[1], datas)
        keys = []
        res = filter(None, map(lambda x: _result_get(x, keys), result))
        res2 = res[:]
        for r in res:
            if isinstance(r[2], dict) and r[2].get('type') in ('ir.actions.report.xml', 'ir.actions.act_window', 'ir.actions.wizard'):
                groups = r[2].get('groups_id')
                if groups:
                    cr.execute('SELECT COUNT(1) FROM res_groups_users_rel WHERE gid IN %s AND uid=%s', (tuple(groups), uid))
                    cnt = cr.fetchone()[0]
                    if not cnt:
                        res2.remove(r)
                    if r[1] == 'Menuitem' and not res2:
                        raise osv.except_osv('Error !', 'You do not have the permission to perform this operation !!!')
        return res2
IrValues()
