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

from osv import osv, fields

class ResUser(osv.osv):
    _inherit = 'res.users'

    _columns = {
        'user_profile': fields.boolean('Is User Profile'),
        'user_profile_id': fields.many2one('res.users', 'User Profile', domain=[('user_profile', '=', True)]),
        'user_ids': fields.one2many('res.users', 'user_profile_id', 'Users', domain=[('user_profile', '=', False)]),
        'field_ids': fields.many2many('ir.model.fields', 'res_users_fields_rel', 'user_id', 'field_id', 'Fields to update',
                                      domain=[('model', '=', 'res.users')]),
    }

    def _get_default_field_ids(self, cr, uid, ids, context=None):
        return self.pool.get('ir.model.fields').search(cr, uid, [
            ('model', '=', 'res.users'),
            ('name', 'in', ('action_id', 'menu_id', 'groups_id', 'view')),
        ], context=context)

    _defaults = {
        'field_ids': _get_default_field_ids,
    }

    def onchange_user_profile(self, cr, uid, ids, user_profile):
        if user_profile:
            return {'value': {'active': False, 'user_profile_id': False}} 
        return {}

    def _get_user_vals_from_profile(self, cr, uid, user_profile_id, context=None):
        vals = {}
        user_profile = self.browse(cr, uid, user_profile_id, context)
        for field in user_profile.field_ids:
            vals[field.name] = user_profile[field.name]
        return vals

    def create(self, cr, uid, vals, context=None):
        if vals.get('user_profile_id'):
            vals.update(self._get_user_vals_from_profile(cr, uid, vals['user_profile_id'], context))
        return super(ResUser, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('user_profile_id'):
            vals.update(self._get_user_vals_from_profile(cr, uid, vals['user_profile_id'], context))
        return super(ResUser, self).write(cr, uid, ids, vals, context)
ResUser()
