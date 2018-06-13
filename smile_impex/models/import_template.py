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

from odoo.addons.smile_log.tools import SmileDBLogger

from ..tools import with_impex_cursor


class IrModelImportTemplate(models.Model):
    _name = 'ir.model.import.template'
    _description = 'Import Template'
    _inherit = 'ir.model.impex.template'

    import_ids = fields.One2many(
        'ir.model.import', 'import_tmpl_id', 'Imports',
        readonly=True, copy=False)
    log_ids = fields.One2many(
        'smile.log', 'res_id', 'Logs',
        domain=[('model_name', '=', 'ir.model.import.template')],
        readonly=True, copy=False)

    def _get_server_action_vals(self, **kwargs):
        vals = super(IrModelImportTemplate, self)._get_server_action_vals(
            **kwargs)
        vals['code'] = "env['ir.model.import.template'].browse(%d)." \
                       "create_import()" % (self.id,)
        return vals

    @api.multi
    @with_impex_cursor()
    def create_import(self, *args):
        self._try_lock(_('Import already in progress'))
        try:
            import_rec = self._create_import(*args)
        except Exception as e:
            tmpl_logger = SmileDBLogger(self._cr.dbname, self._name,
                                        self.id, self._uid)
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
