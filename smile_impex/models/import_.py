# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import inspect

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class IrModelImport(models.Model):
    _name = 'ir.model.import'
    _description = 'Import'
    _inherit = 'ir.model.impex'

    import_tmpl_id = fields.Many2one(
        'ir.model.import.template', 'Template',
        readonly=True, required=True,
        ondelete='cascade', index=True)
    log_ids = fields.One2many(
        'smile.log', 'res_id', 'Logs', readonly=True,
        domain=[('model_name', '=', 'ir.model.import')])

    def _execute(self):
        self.ensure_one()
        model_obj = self.env[self.import_tmpl_id.model_id.model]
        if self._context.get('original_cr') and \
                not self._context.get('force_use_new_cursor'):
            new_env = self.env(cr=self._context['original_cr'])
            model_obj = model_obj.with_env(new_env)
        args = safe_eval(self.args or '[]')
        kwargs = safe_eval(self.import_tmpl_id.method_args or '{}')
        return getattr(model_obj, self.import_tmpl_id.method)(*args, **kwargs)

    @api.model
    def init(self):
        super().init()
        callers = [frame[3] for frame in inspect.stack()]
        if 'preload_registries' in callers:
            self._kill_impex()
