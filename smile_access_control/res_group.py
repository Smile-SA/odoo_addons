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

from osv import osv

class IrModel(osv.osv):
    _inherit = 'ir.model'

    def _get_first_level_relations(self, cr, uid, ids, context):
        field_obj = self.pool.get('ir.model.fields')
        field_ids = field_obj.search(cr, uid, [
            ('ttype', 'in', ('many2one', 'one2many', 'many2many')),
            ('model_id', 'in', ids),
        ], context=context)
        if field_ids:
            models = [field['relation'] for field in field_obj.read(cr, uid, field_ids, ['relation'], context=None)]
            return self.search(cr, uid, [('model', 'in', models)], context=context)
        return []

    def get_relations(self, cr, uid, ids, level=1, context=None):
        """
        Return models linked to models given in params
        If you don't want limit the relations level, indicate level = -1
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        relation_ids, model_ids = list(ids), list(ids)
        while model_ids and level:
            model_ids = self._get_first_level_relations(cr, uid, model_ids, context)
            model_ids = list(set(model_ids) - set(relation_ids))
            relation_ids.extend(model_ids)
            level -= 1
        return list(set(relation_ids) - set(ids))
IrModel()

class IrModelAccess(osv.osv):
    _inherit = 'ir.model.access'

    def get_name(self, cr, uid, model_id, group_id=False):
        model = self.pool.get('ir.model').read(cr, uid, model_id, ['model'])['model']
        group = group_id and self.pool.get('res.groups').read(cr, uid, group_id, ['name'])['name'].lower() or 'all'
        return '%s %s' % (model, group)
IrModelAccess()

class ResGroup(osv.osv):
    _inherit = 'res.groups'

    def button_complete_access_controls(self, cr, uid, ids, context=None):
        """Create access rules for the first level relation models of access rule models not only in readonly"""
        context = context or {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        access_obj = self.pool.get('ir.model.access')
        for group in self.browse(cr, uid, ids, context):
            model_ids = [access_rule.model_id.id for access_rule in group.model_access \
                         if access_rule.perm_write or access_rule.perm_create or access_rule.perm_unlink]
            relation_model_ids = self.pool.get('ir.model').get_relations(cr, uid, model_ids, context.get('relations_level', 1), context)
            for relation_model_id in relation_model_ids:
                access_obj.create(cr, uid, {
                    'name': access_obj.get_name(cr, uid, relation_model_id, group.id),
                    'model_id': relation_model_id,
                    'group_id': group.id,
                    'perm_read': True,
                    'perm_write': False,
                    'perm_create': False,
                    'perm_unlink': False,
                }, context)
        return True

    def _update_users(self, cr, uid, vals, context=None):
        if vals.get('users'):
            user_profile_ids = []
            user_obj = self.pool.get('res.users')
            for item in vals['users']:
                user_ids = []
                if item[0] == 6:
                    user_ids = item[2]
                elif item[0] == 4:
                    user_ids = [item[1]]
                for user in user_obj.read(cr, uid, user_ids, ['user_profile', 'user_profile_id'], context, '_classic_write'):
                    if user['user_profile']:
                        user_profile_ids.append(user['id'])
                    else:
                        user_profile_ids.append(user['user_profile_id'])
            if user_profile_ids:
                user_obj.write(cr, uid, list(set(user_profile_ids)), {}, context) # Update users linked to profiles

    def write(self, cr, uid, ids, vals, context=None):
        self._update_users(cr, uid, vals, context)
        return super(ResGroup, self).write(cr, uid, ids, vals, context)
ResGroup()

