# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, fields, models


class WizardIrModelMethods(models.TransientModel):
    _name = 'wizard.ir.model.methods'
    _description = 'Wizard Model Method'
    _rec_name = ''

    models_id = fields.Many2many('ir.model', 'ir_model_methotds_rel', 'wizard_model_id', 'model_id', string="Model list")
    to_update = fields.Boolean("Update lines ?")

    @api.multi
    def button_call(self):
        self.ensure_one()
        self.env['ir.model.methods'].with_context(to_update=self.to_update).update_list(self.models_id.mapped('model'))
