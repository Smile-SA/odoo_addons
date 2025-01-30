# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
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
        vals = super()._get_server_action_vals(**kwargs)
        vals['code'] = "env['ir.model.import.template'].browse(%d)." \
                       "create_import()" % (self.id,)
        return vals

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

    def _create_import(self, *args):
        vals = self._get_import_vals(*args)
        return self.env['ir.model.import'].create(vals)

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
