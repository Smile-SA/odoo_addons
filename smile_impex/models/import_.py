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
from openerp.modules.registry import Registry

from openerp.addons.smile_log.tools import SmileDBLogger
from openerp.addons.smile_impex.models.impex import IrModelImpex, IrModelImpexTemplate, state_cleaner
from openerp.addons.smile_impex.tools.api import with_new_cursor


class IrModelImportTemplate(models.Model, IrModelImpexTemplate):
    _name = 'ir.model.import.template'
    _description = 'Import Template'

    import_ids = fields.One2many('ir.model.import', 'import_tmpl_id', 'Imports', readonly=True)
    log_ids = fields.One2many('smile.log', 'res_id', 'Logs', domain=[('model_name', '=', 'ir.model.import.template')], readonly=True)

    def _get_cron_vals(self):
        vals = super(IrModelImportTemplate, self)._get_cron_vals()
        vals['function'] = 'create_import'
        return vals

    def _get_server_action_vals(self, model_id):
        vals = super(IrModelImportTemplate, self)._get_server_action_vals(self, model_id)
        vals['code'] = "self.pool.get('ir.model.import.template').create_import(cr, uid, %d, context)" % (self.id,)
        return vals

    @api.one
    @api.returns('ir.model.import', lambda value: value.id)
    def create_import(self):
        try:
            import_obj = self.env['ir.model.import']
            vals = {
                'import_tmpl_id': self.id,
                'test_mode': self._context.get('test_mode', False),
            }
            import_rec = import_obj.create(vals)
            import_rec.process()
            return import_rec
        except Exception, e:
            tmpl_logger = SmileDBLogger(self._cr.dbname, self._name, self.id, self._uid)
            tmpl_logger.error(repr(e))
            raise Warning(repr(e))


class IrModelImport(models.Model, IrModelImpex):
    _name = 'ir.model.import'
    _description = 'Import'

    def __init__(self, pool, cr):
        super(IrModelImport, self).__init__(pool, cr)
        setattr(Registry, 'load', state_cleaner(pool[self._name])(getattr(Registry, 'load')))

    import_tmpl_id = fields.Many2one('ir.model.import.template', 'Template', readonly=True, required=True, ondelete='cascade')
    log_ids = fields.One2many('smile.log', 'res_id', 'Logs', domain=[('model_name', '=', 'ir.model.import')], readonly=True)

    @api.one
    @with_new_cursor
    def _execute(self):
        model_obj = self.env[self.import_tmpl_id.model_id.model].browse()
        getattr(model_obj, self.import_tmpl_id.method)(**eval(self.import_tmpl_id.method_args or '{}'))
