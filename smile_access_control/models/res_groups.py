# -*- coding: utf-8 -*-
# (C) 2011 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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
        # INFO: it's not useful to call this inside create method because
        # natively ResGroups.create calls ResGroups.write({'users': [...]})
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
        """ Improve performance of method, by not link group always linked,
        and not tryging to remove group always removed.
        """
        if 'implied_ids' in vals:
            for group in self:
                group_vals = vals.copy()
                new_implied_ids = []
                for implied in group_vals['implied_ids']:
                    magic_number = implied[0]
                    if magic_number == 3:
                        group_to_remove_id = implied[1]
                        if group_to_remove_id not in group.implied_ids.ids:
                            continue
                    elif magic_number == 4:
                        group_to_add_id = implied[1]
                        if group_to_add_id in group.implied_ids.ids:
                            continue
                    elif magic_number == 5:
                        new_implied_ids = []
                    elif magic_number == 6:
                        new_implied_ids = [implied]
                    new_implied_ids.append(implied)
                # Check last element, maybe erasing all previous elements,
                # except for 0, 1, 2 magic numbers
                if new_implied_ids:
                    last_new_implied = new_implied_ids[-1]
                    new_implied_ids_to_keep = [
                        new_implied_id
                        for new_implied_id in new_implied_ids
                        if new_implied_id[0] in range(3)
                    ]
                    if last_new_implied[0] == 5:
                        if group.implied_ids.ids == []:
                            new_implied_ids = new_implied_ids_to_keep
                        else:
                            new_implied_ids = new_implied_ids_to_keep + \
                                [last_new_implied]
                    elif last_new_implied[0] == 6:
                        if group.implied_ids.ids == last_new_implied[2]:
                            new_implied_ids = new_implied_ids_to_keep
                        else:
                            new_implied_ids = new_implied_ids_to_keep + \
                                [last_new_implied]
                group_vals['implied_ids'] = new_implied_ids
                res = super(ResGroups, group).write(group_vals)
        else:
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
