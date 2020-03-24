# -*- coding: utf-8 -*-
# (C) 2011 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.depends('groups_id')
    def _compute_share(self):
        for user in self:
            user.share = user.is_user_profile or \
                not user.has_group('base.group_user')

    @api.model
    def _get_default_field_ids(self):
        return self.env['ir.model.fields'].search([
            ('model', 'in', ('res.users', 'res.partner')),
            ('name', 'in', ('action_id', 'menu_id', 'groups_id')),
        ]).ids

    is_user_profile = fields.Boolean('Is User Profile', oldname='user_profile')
    user_profile_id = fields.Many2one(
        'res.users', 'User Profile',
        domain=[('id', '!=', SUPERUSER_ID), ('is_user_profile', '=', True)],
        context={'active_test': False})
    user_ids = fields.One2many(
        'res.users', 'user_profile_id', 'Users',
        domain=[('is_user_profile', '=', False)])
    field_ids = fields.Many2many(
        'ir.model.fields', 'res_users_fields_rel', 'user_id', 'field_id',
        'Fields to update',
        domain=[
            ('model', 'in', ('res.users', 'res.partner')),
            ('ttype', 'not in', ('one2many',)),
            ('name', 'not in', ('is_user_profile', 'user_profile_id',
                                'user_ids', 'field_ids', 'view'))],
        default=_get_default_field_ids)
    is_update_users = fields.Boolean(
        string="Update users after creation", default=lambda *a: True,
        help="If non checked, users associated to this profile "
        "will not be updated after creation")
    users_count = fields.Integer(compute='_compute_users_count')

    _sql_constraints = [
        ('active_admin_check', 'CHECK (id = 2 AND active = TRUE OR id <> 2)',
         'The user with id = 2 must always be active!'),
        ('profile_without_profile_id',
         'CHECK( (is_user_profile = TRUE AND user_profile_id IS NULL) OR '
         'is_user_profile = FALSE )',
         'Profile users cannot be linked to a profile!'),
    ]

    @api.one
    @api.constrains('user_profile_id')
    def _check_user_profile_id(self):
        admin = self.env.ref('base.user_root')
        if self.user_profile_id == admin:
            raise ValidationError(
                _("You can't use %s as user profile !") % admin.name)

    @api.one
    def _compute_users_count(self):
        self.users_count = len(self.user_ids)

    @api.onchange('is_user_profile')
    def onchange_user_profile(self):
        if self.is_user_profile:
            self.active = self.id == SUPERUSER_ID
            self.user_profile_id = False

    @api.multi
    def _update_from_profile(self, fields=None):
        if not self:
            return
        if len(self.mapped('user_profile_id')) != 1:
            raise UserError(
                _("_update_from_profile accepts only users "
                    "linked to a same profile"))
        user_profile = self[0].user_profile_id
        if not fields:
            fields = user_profile.field_ids.mapped('name')
        else:
            fields = set(fields) & set(user_profile.field_ids.mapped('name'))
        if user_profile:
            vals = {}
            for field in fields:
                value = user_profile[field]
                field_type = self._fields[field].type
                if field_type == 'many2one':
                    vals[field] = value.id
                elif field_type == 'many2many':
                    vals[field] = [(6, 0, value.ids)]
                elif field_type == 'one2many':
                    raise UserError(
                        _("_update_from_profile doesn't manage "
                            "fields.One2many"))
                else:
                    vals[field] = value
            if vals:
                self.write(vals)

    @api.multi
    def _update_users_linked_to_profile(self, fields=None):
        for user_profile in self.filtered(
                lambda user: user.is_user_profile and user.is_update_users):
            user_profile.with_context(active_test=False).mapped(
                'user_ids')._update_from_profile(fields)

    @api.model
    def create(self, vals):
        record = super(ResUsers, self).create(vals)
        if record.user_profile_id:
            record._update_from_profile()
        return record

    @api.multi
    def write(self, vals):
        if vals.get('user_profile_id'):
            users_to_update = self.filtered(
                lambda user: user.user_profile_id.id != vals[
                    'user_profile_id'])
        vals = self._remove_reified_groups(vals)
        res = super(ResUsers, self).write(vals)
        if vals.get('user_profile_id'):
            users_to_update._update_from_profile()
        else:
            self._update_users_linked_to_profile(list(vals.keys()))
        return res
