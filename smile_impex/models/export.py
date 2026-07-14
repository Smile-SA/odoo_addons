# -*- coding: utf-8 -*-
# (C) 2026 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import inspect

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class IrModelExport(models.Model):
    _name = 'ir.model.export'
    _description = 'Export'
    _inherit = 'ir.model.impex'

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

    def _execute(self):
        self.ensure_one()
        if not self.record_ids:
            raise UserError(
                _("You cannot regenerate this export "
                  "because records to export didn't store"))

        record_ids = safe_eval(self.record_ids)

        if not (record_ids or self.export_tmpl_id.force_execute_action):
            return None
        if not self.export_tmpl_id.method:
            return None
        records = self._get_records_to_export(record_ids)
        args = safe_eval(self.args or '[]')
        kwargs = safe_eval(self.export_tmpl_id.method_args or '{}')
        return getattr(records, self.export_tmpl_id.method)(*args, **kwargs)

    @api.model
    def init(self):
        super().init()
        callers = [frame[3] for frame in inspect.stack()]
        if 'preload_registries' in callers:
            self._kill_impex()

    def _get_records_to_export(self, record_ids):
        """
        Get the records to export, considering the export template and the
        context.

        :param record_ids: The IDs of the records to export.
        :return: The records to export.
        """
        records = self.env[self.export_tmpl_id.model_id.model].browse(
            record_ids).with_context(export_tmpl_id=self.export_tmpl_id.id)
        if self._should_use_original_cursor():
            new_env = self.env(
                cr=self._context['original_cr'],
                context=records._context)
            records = records.with_env(new_env)
        return records

    def _should_use_original_cursor(self):
        """
        Check if the current cursor is the one used in the original request.
        This is useful when we need to make sure that we don't use a new cursor
        in the context of the current request, as it can lead to issues with
        database locks.

        :return: True if the original cursor should be used, False otherwise.
        """
        return bool(self._context.get('original_cr')) and \
            not self._context.get('force_use_new_cursor')
