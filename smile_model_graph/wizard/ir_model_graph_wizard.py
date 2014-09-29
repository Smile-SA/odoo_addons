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


class IrModelGraphWizard(models.TransientModel):
    _name = 'ir.model.graph_wizard'
    _description = 'Model Graph Wizard'
    _rec_name = 'filename'

    deep = fields.Integer(required=True, default=True)
    show_relation_name = fields.Boolean('Show Relation Name')
    file = fields.Binary(filename='filename', readonly=True)
    filename = fields.Char(required=True, default='model_graph.png')

    @api.multi
    def button_generate_file(self):
        self.ensure_one()
        model_obj = self.env['ir.model']
        if self._context.get('active_ids'):
            for wizard in self:
                models = model_obj.browse(self._context['active_ids'])
                data = models.get_graph(wizard.deep, wizard.show_relation_name, None)
                wizard.write({'file': data})
        return {
            "type": "ir.actions.act_window",
            "name": "Models Graph",
            "res_model": "ir.model.graph_wizard",
            "view_type": "form",
            "view_mode": "form",
            "res_id": self._ids[0],
            "target": 'new',
            "context": self._context,
        }
