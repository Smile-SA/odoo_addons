# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


from odoo import models


class WizardModelMenu(models.TransientModel):
    _inherit = 'wizard.ir.model.menu.create'

    def menu_create(self):
        """ Override menu_create function to set the value of the field is_customized_menu
        to True when creating a new menu through the 'create menu' button"""
        for menu in self:
            model = self.env['ir.model'].browse(self._context.get('model_id'))
            vals = {
                'name': menu.name,
                'res_model': model.model,
                'view_mode': 'tree,form',
            }
            action_id = self.env['ir.actions.act_window'].create(vals)
            self.env['ir.ui.menu'].create({
                'name': menu.name,
                'parent_id': menu.menu_id.id,
                'action': 'ir.actions.act_window,%d' % (action_id,),
                'is_customized_menu': True,
            })
        return {'type': 'ir.actions.act_window_close'}
