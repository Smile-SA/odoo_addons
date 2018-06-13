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

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.modules.registry import Registry
from odoo.tools.safe_eval import safe_eval

from odoo.addons.smile_impex.models.impex import state_cleaner


class IrModelExport(models.Model):
    _name = 'ir.model.export'
    _description = 'Export'
    _inherit = 'ir.model.impex'

    def __init__(self, pool, cr):
        super(IrModelExport, self).__init__(pool, cr)
        model = pool[self._name]
        if not getattr(model, '_state_cleaner', False):
            model._state_cleaner = True
            setattr(Registry, 'setup_models', state_cleaner(model)(
                getattr(Registry, 'setup_models')))

    export_tmpl_id = fields.Many2one(
        'ir.model.export.template', 'Template', readonly=True, required=True,
        ondelete='cascade', index=True)
    log_ids = fields.One2many(
        'smile.log', 'res_id', 'Logs', readonly=True,
        domain=[('model_name', '=', 'ir.model.export')])
    offset = fields.Integer()
    record_ids = fields.Text(
        'Records', readonly=True, required=True, default='[]')
    record_count = fields.Integer('# Records')

    @api.multi
    def _execute(self):
        self.ensure_one()
        if not self.record_ids:
            raise UserError(
                _("You cannot regenerate this export "
                  "because records to export didn't store"))
        record_ids = safe_eval(self.record_ids)
        if record_ids or self.export_tmpl_id.force_execute_action:
            records = self.env[self.export_tmpl_id.model_id.model].browse(
                record_ids)
            if self.export_tmpl_id.method:
                if self._context.get('original_cr'):
                    new_env = self.env(cr=self._context['original_cr'])
                    records = records.with_env(new_env)
                args = safe_eval(self.args or '[]')
                kwargs = safe_eval(self.export_tmpl_id.method_args or '{}')
                return getattr(records, self.export_tmpl_id.method)(
                    *args, **kwargs)
