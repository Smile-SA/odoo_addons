# -*- coding: utf-8 -*-
# (C) 2011 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class IrModel(models.Model):
    _inherit = 'ir.model'

    @api.multi
    def _get_first_level_relations(self):
        Fields = self.env['ir.model.fields']
        field_recs = Fields.search([
            ('ttype', 'in', ('many2one', 'one2many', 'many2many')),
            ('model_id', 'in', self.ids),
        ])
        return self.search([('model', 'in', field_recs.mapped('relation'))])

    @api.multi
    def _get_relations(self, level=1):
        """
        Return models linked to models given in params
        If you don't want limit the relations level, indicate level = -1
        """
        relations = self
        while self and level:
            self = self._get_first_level_relations() - relations
            relations |= self
            level -= 1
        return self


class ResGroups(models.Model):
    _inherit = 'res.groups'

    active = fields.Boolean(default=True)

    @api.multi
    def _update_users(self, vals):
        if vals.get('users'):
            Users = self.env['res.users']
            user_profiles = Users.browse()
            for item in vals['users']:
                user_ids = []
                if item[0] == 6:
                    user_ids = item[2]
                elif item[0] == 4:
                    user_ids = [item[1]]
                users = Users.browse(user_ids)
                user_profiles |= users.filtered(
                    lambda user: user.is_user_profile)
                user_profiles |= users.mapped('user_profile_id')
            if user_profiles:
                user_profiles._update_users_linked_to_profile()

    @api.multi
    def write(self, vals):
        # INFO: it's not useful to override create method because
        # natively ResGroups.create calls ResGroups.write({'users': [...]})
        res = super(ResGroups, self).write(vals)
        self._update_users(vals)
        return res

    @api.multi
    def button_complete_access_controls(self):
        """Create access rules for the first level relation models
        # of access rule models not only in readonly"""
        def filter_rule(rule):
            return rule.perm_write or rule.perm_create or rule.perm_unlink
        Access = self.env['ir.model.access']
        for group in self:
            models = group.model_access.filtered(
                filter_rule).mapped('model_id')
            for model in models._get_relations(
                    self._context.get('relations_level', 1)):
                Access.create({
                    'name': '%s %s' % (model.model, group.name),
                    'model_id': model.id,
                    'group_id': group.id,
                    'perm_read': True,
                    'perm_write': False,
                    'perm_create': False,
                    'perm_unlink': False,
                })
        return True
