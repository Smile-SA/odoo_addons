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

from openerp import api, fields, models, _
from openerp.exceptions import UserError
from openerp.modules.registry import Registry
from openerp.tools.safe_eval import safe_eval as eval

from openerp.addons.smile_log.tools import SmileDBLogger
from openerp.addons.smile_impex.models.impex import state_cleaner

from ..tools import with_impex_cursor


class IrModelImportTemplate(models.Model):
    _name = 'ir.model.import.template'
    _description = 'Import Template'
    _inherit = 'ir.model.impex.template'

    import_ids = fields.One2many('ir.model.import', 'import_tmpl_id', 'Imports', readonly=True, copy=False)
    log_ids = fields.One2many('smile.log', 'res_id', 'Logs', domain=[('model_name', '=', 'ir.model.import.template')],
                              readonly=True, copy=False)

    def _get_cron_vals(self, **kwargs):
        vals = super(IrModelImportTemplate, self)._get_cron_vals(**kwargs)
        vals['function'] = 'create_import'
        return vals

    def _get_server_action_vals(self, model_id, **kwargs):
        vals = super(IrModelImportTemplate, self)._get_server_action_vals(model_id, **kwargs)
        vals['code'] = "self.pool.get('ir.model.import.template').create_import(cr, uid, %d, context)" % (self.id,)
        return vals

    @api.multi
    @with_impex_cursor()
    def create_import(self, *args):
        self._try_lock(_('Import already in progress'))
        try:
            import_rec = self._create_import(*args)
        except Exception, e:
            tmpl_logger = SmileDBLogger(self._cr.dbname, self._name, self.id, self._uid)
            tmpl_logger.error(repr(e))
            raise UserError(repr(e))
        else:
            return import_rec.process()

    @api.multi
    def _create_import(self, *args):
        vals = self._get_import_vals(*args)
        return self.env['ir.model.import'].create(vals)

    @api.multi
    def _get_import_vals(self, *args):
        self.ensure_one()
        return {
            'import_tmpl_id': self.id,
            'test_mode': self._context.get('test_mode'),
            'new_thread': self._context.get('new_thread', self.new_thread),
            'args': repr(args),
            'log_level': self.log_level,
            'log_returns': self.log_returns,
        }


class IrModelImport(models.Model):
    _name = 'ir.model.import'
    _description = 'Import'
    _inherit = 'ir.model.impex'

    def __init__(self, pool, cr):
        super(IrModelImport, self).__init__(pool, cr)
        setattr(Registry, 'setup_models', state_cleaner(pool[self._name])(getattr(Registry, 'setup_models')))

    import_tmpl_id = fields.Many2one('ir.model.import.template', 'Template', readonly=True, required=True,
                                     ondelete='cascade', index=True)
    log_ids = fields.One2many('smile.log', 'res_id', 'Logs', readonly=True,
                              domain=[('model_name', '=', 'ir.model.import')])

    @api.multi
    def _execute(self):
        self.ensure_one()
        model_obj = self.env[self.import_tmpl_id.model_id.model]
        if self._context.get('original_cr'):
            new_env = self.env(cr=self._context['original_cr'])
            model_obj = model_obj.with_env(new_env)
        args = eval(self.args or '[]')
        kwargs = eval(self.import_tmpl_id.method_args or '{}')
        return getattr(model_obj, self.import_tmpl_id.method)(*args, **kwargs)
