# -*- coding: utf-8 -*-
# (C) 2014 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.modules.registry import Registry
from odoo.tools.safe_eval import safe_eval

from odoo.addons.smile_impex.models.impex import state_cleaner


class IrModelImport(models.Model):
    _name = 'ir.model.import'
    _description = 'Import'
    _inherit = 'ir.model.impex'

    def __init__(self, pool, cr):
        super(IrModelImport, self).__init__(pool, cr)
        model = pool[self._name]
        if not getattr(model, '_state_cleaner', False):
            model._state_cleaner = True
            setattr(Registry, 'setup_models', state_cleaner(model)(
                getattr(Registry, 'setup_models')))

    import_tmpl_id = fields.Many2one(
        'ir.model.import.template', 'Template',
        readonly=True, required=True,
        ondelete='cascade', index=True)
    log_ids = fields.One2many(
        'smile.log', 'res_id', 'Logs', readonly=True,
        domain=[('model_name', '=', 'ir.model.import')])

    @api.multi
    def _execute(self):
        self.ensure_one()
        model_obj = self.env[self.import_tmpl_id.model_id.model]
        if self._context.get('original_cr'):
            new_env = self.env(cr=self._context['original_cr'])
            model_obj = model_obj.with_env(new_env)
        args = safe_eval(self.args or '[]')
        kwargs = safe_eval(self.import_tmpl_id.method_args or '{}')
        return getattr(model_obj, self.import_tmpl_id.method)(*args, **kwargs)
