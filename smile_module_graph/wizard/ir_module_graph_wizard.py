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

from osv import orm, fields


class IrModuleGraphWizard(orm.TransientModel):
    _name = 'ir.module.module.graph_wizard'
    _description = 'Module Graph Wizard'

    _columns = {
        'stream': fields.selection([('down', 'Down'), ('up', 'Up'), ('up-down', 'Up & Down')], 'Stream', required=True),
        'uninstallable': fields.boolean('Uninstallable'),
        'uninstalled': fields.boolean('Not Installed'),
        'installed': fields.boolean('Installed'),
        'file': fields.binary('File', filename='filename', readonly=True),
        'filename': fields.char('Filename', size=64, required=True),
    }

    _defaults = {
        'stream': 'down',
        'uninstallable': True,
        'uninstalled': True,
        'installed': True,
        'filename': 'module_graph.png',
    }

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

    def button_generate_file(self, cr, uid, ids, context=None):
        context = context or {}
        module_obj = self.pool.get('ir.module.module')
        for wizard in self.browse(cr, uid, ids, context):
            states = IrModuleGraphWizard._get_states(wizard)
            data = module_obj.get_graph(cr, uid, context.get('active_ids', []), stream=wizard.stream,
                                        states=states, path=None, context=context)
            wizard.write({'file': data})
        return True
