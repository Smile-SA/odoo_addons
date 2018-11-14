# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class IrModelGraphWizard(models.TransientModel):
    _name = 'ir.model.graph_wizard'
    _description = 'Models Graph Wizard'
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
                data = models.get_graph(wizard.deep, wizard.show_relation_name,
                                        None)
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
