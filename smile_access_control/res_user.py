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

from openerp.osv import orm, fields
from openerp.tools.translate import _


class ResUsers(orm.Model):
    _inherit = 'res.users'

    _columns = {
        'user_profile': fields.boolean('Is User Profile'),
        'user_profile_id': fields.many2one('res.users', 'User Profile', domain=[('user_profile', '=', True)], context={'active_test': False}),
        'user_ids': fields.one2many('res.users', 'user_profile_id', 'Users', domain=[('user_profile', '=', False)]),
        'field_ids': fields.many2many('ir.model.fields', 'res_users_fields_rel', 'user_id', 'field_id', 'Fields to update',
                                      domain=[('model', '=', 'res.users'),
                                              ('name', 'not in', ('user_profile', 'user_profile_id', 'user_ids', 'field_ids', 'view'))]),
    }

    def _get_default_field_ids(self, cr, uid, context=None):
        return self.pool.get('ir.model.fields').search(cr, uid, [
            ('model', '=', 'res.users'),
            ('name', 'in', ('action_id', 'menu_id', 'groups_id')),
        ], context=context)

    _defaults = {
        'field_ids': _get_default_field_ids,
    }

    _sql_constraints = [
        ('active_admin_check', 'CHECK (id = 1 AND active = TRUE OR id <> 1)', 'The user with id = 1 must be always active!'),
        ('profile_without_profile_id', 'CHECK( (user_profile = TRUE AND user_profile_id IS NULL) OR user_profile = FALSE )',
         'Profile users cannot be linked to a profile!'),
    ]

    def onchange_user_profile(self, cr, uid, ids, user_profile):
        if user_profile:
            return {'value': {'active': ids == [1] and True or False, 'user_profile_id': False}}
        return {}

    def _get_user_vals_from_profile(self, cr, uid, user_profile_id, context=None):
        vals = {}
        user_profile = self.read(cr, uid, user_profile_id)
        for field in self.pool.get('ir.model.fields').read(cr, uid, user_profile['field_ids'], ['name']):
            value = user_profile[field['name']]
            if isinstance(value, tuple):
                value = value[0]
            if isinstance(value, list):
                value = [(6, 0, value)]
            vals[field['name']] = value
        vals['user_ids'] = [(5, 0)]
        return vals

    def create(self, cr, uid, vals, context=None):
        if vals.get('user_profile_id'):
            vals.update(self._get_user_vals_from_profile(cr, uid, vals['user_profile_id'], context))
        return super(ResUsers, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if not ids:
            return True
        if isinstance(ids, (int, long)):
            ids = [ids]
        if vals.get('user_profile_id'):
            new_profile_user_ids = []
            same_profile_user_ids = []
            for user in self.read(cr, uid, ids, ['user_profile', 'user_profile_id'], context, '_classic_write'):
                if user['user_profile'] and vals.get('user_profile', True):
                    raise orm.except_orm(_('Warning!'), _('You cannot change the profile of a user which is itself a profile!'))
                if user['user_profile_id'] == vals['user_profile_id']:
                    same_profile_user_ids.append(user['id'])
                else:
                    new_profile_user_ids.append(user['id'])
            if same_profile_user_ids:
                super(ResUsers, self).write(cr, uid, same_profile_user_ids, vals, context)
            if new_profile_user_ids:
                vals.update(self._get_user_vals_from_profile(cr, uid, vals['user_profile_id'], context))
                super(ResUsers, self).write(cr, uid, new_profile_user_ids, vals, context)
        else:
            super(ResUsers, self).write(cr, uid, ids, vals, context)
            for user_profile in self.browse(cr, uid, ids, context):
                if user_profile.user_profile and user_profile.user_ids and any(field.name in vals for field in user_profile.field_ids):
                    profile_vals = self._get_user_vals_from_profile(cr, uid, user_profile.id, context)
                    self.write(cr, uid, [user.id for user in user_profile['user_ids']], profile_vals, context)
        return True

    def copy_data(self, cr, uid, user_id, default=None, context=None):
        default = default.copy() if default else {}
        default['user_ids'] = []
        return super(ResUsers, self).copy_data(cr, uid, user_id, default, context)
