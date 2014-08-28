# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp import api, fields, models


class IrModuleGraphWizard(models.TransientModel):
    _name = 'ir.module.module.graph_wizard'
    _description = 'Module Graph Wizard'
    _rec_name = 'filename'

    stream = fields.Selection([('down', 'Down'), ('up', 'Up'), ('up-down', 'Up & Down')], required=True, default='up')
    uninstallable = fields.Boolean()
    uninstalled = fields.Boolean('Not Installed')
    installed = fields.Boolean(default=True)
    file = fields.Binary(filename='filename', readonly=True)
    filename = fields.Char(required=True, default='module_graph.png')

    @staticmethod
    def _get_states(wizard):
        states = []
        if wizard.uninstallable:
            states.extend(['uninstallable', 'unknown'])
        if wizard.uninstalled:
            states.extend(['uninstalled', 'to install'])
        if wizard.installed:
            states.extend(['installed', 'to upgrade', 'to remove'])
        return states

    @api.multi
    def button_generate_file(self):
        assert len(self) == 1, 'ids must be a list with only one item!'
        module_obj = self.env['ir.module.module']
        for wizard in self:
            states = IrModuleGraphWizard._get_states(wizard)
            modules = module_obj.browse(self._context['active_ids'])
            data = modules.get_graph(wizard.stream, states, None)
            wizard.write({'file': data})
        return {
            "type": "ir.actions.act_window",
            "name": "Modules Graph",
            "res_model": "ir.module.module.graph_wizard",
            "view_type": "form",
            "view_mode": "form",
            "res_id": self._ids[0],
            "target": 'new',
            "context": self._context,
        }
