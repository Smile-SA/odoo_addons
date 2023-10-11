# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

from odoo.addons.smile_log.tools import SmileDBLogger

from ..tools import with_impex_cursor


class IrModelExportTemplate(models.Model):
    _name = 'ir.model.export.template'
    _description = 'Export Template'
    _inherit = 'ir.model.impex.template'

    export_ids = fields.One2many(
        'ir.model.export', 'export_tmpl_id', 'Exports',
        readonly=True, copy=False)
    log_ids = fields.One2many(
        'smile.log', 'res_id', 'Logs',
        domain=[('model_name', '=', 'ir.model.export.template')],
        readonly=True, copy=False)

    client_action = fields.Boolean(compute='_get_client_action', store=True)
    filter_type = fields.Selection(
        [('domain', 'Domain'), ('method', 'Method')],
        required=True, default='domain')
    filter_domain = fields.Text(
        default='[]', help="Available variables: context, time, user")
    filter_method = fields.Char(help="signature: @api.model + *args")
    limit = fields.Integer()
    max_offset = fields.Integer()
    order = fields.Char('Order by')
    unique = fields.Boolean(
        help="If unique, each record is exported only once")
    force_execute_action = fields.Boolean(
        'Force Action Execution', help="Even if there are no record to export")
    do_not_store_record_ids = fields.Boolean(
        'Do not store exported records',
        help="If checked, export regeneration will not be possible")

    @api.depends('server_action_id.binding_model_id')
    def _get_client_action(self):
        for template in self:
            template.client_action = bool(
                template.server_action_id.binding_model_id)

    @api.constrains('unique', 'do_not_store_record_ids')
    def _check_export_template_config(self):
        if any(template.unique and template.do_not_store_record_ids
               for template in self):
            raise UserError(
                _('Exported records storing is required '
                  'if export must be unique'))

    def _get_server_action_vals(self, **kwargs):
        vals = super()._get_server_action_vals(**kwargs)
        if vals:
            vals['code'] = "env['ir.model.export.template']." \
                           "browse(%d).create_export()" % (self.id,)
        return vals

    def create_client_action(self, **kwargs):
        self.ensure_one()
        if not self.server_action_id:
            self.create_server_action()
        if not self.server_action_id.binding_model_id:
            self.server_action_id.binding_model_id = self.model_id
        return True

    def unlink_client_action(self):
        self.ensure_one()
        if self.server_action_id:
            self.server_action_id.unlink()
        return True

    def _get_eval_context(self):
        return {'context': self._context, 'user': self.env.user}

    def _get_res_ids(self, *args):
        model_obj = self.env[self.model_id.model]
        if self._context.get('original_cr'):
            model_obj = model_obj.with_env(
                self.env(cr=self._context['original_cr']))
        if self.filter_type == 'domain':
            domain = safe_eval(self.filter_domain or '[]',
                               self._get_eval_context())
            res_ids = set(model_obj.search(
                domain, order=self.order or '')._ids)
        else:  # elif self.filter_type == 'method':
            if not (self.filter_method and hasattr(
                    model_obj, self.filter_method)):
                raise UserError(_("Can't find method: %s on object: %s") % (
                    self.filter_method, self.model_id.model))
            res_ids = set(getattr(model_obj, self.filter_method)(*args))
        if 'active_ids' in self._context:
            res_ids &= set(self._context['active_ids'])
        if self.unique:
            res_ids -= set(sum([safe_eval(export.record_ids)
                                for export in self.export_ids], []))
        return list(res_ids)

    def _get_res_ids_offset(self, *args):
        """Get records and split them in groups
        in function of limit and max_offset"""
        res_ids = self._get_res_ids(*args)
        if self.limit:
            res_ids_list = []
            i = 0
            while res_ids[i: i + self.limit]:
                if self.max_offset and i == self.max_offset * self.limit:
                    break
                res_ids_list.append(res_ids[i: i + self.limit])
                i += self.limit
            return res_ids_list
        return [res_ids]

    @with_impex_cursor()
    def create_export(self, *args):
        self._try_lock(_('Export already in progress'))
        try:
            export_recs = self._create_export(*args)
        except Exception as e:
            tmpl_logger = SmileDBLogger(
                self._cr.dbname, self._name, self.id, self._uid)
            tmpl_logger.error(repr(e))
            raise UserError(repr(e))
        else:
            res = export_recs.process()
            if self.do_not_store_record_ids:
                export_recs.write({'record_ids': ''})
            return res

    def _create_export(self, *args):
        export_recs = self.env['ir.model.export'].browse()
        vals = self._get_export_vals(*args)
        for index, res_ids_offset in \
                enumerate(self._get_res_ids_offset(*args)):
            vals['record_ids'] = res_ids_offset
            vals['record_count'] = len(res_ids_offset)
            vals['offset'] = index + 1
            export_recs |= export_recs.create(vals)
        return export_recs

    def _get_export_vals(self, *args):
        self.ensure_one()
        return {
            'export_tmpl_id': self.id,
            'test_mode': self._context.get('test_mode'),
            'new_thread': self._context.get('new_thread', self.new_thread),
            'args': repr(args),
            'log_level': self.log_level,
            'log_returns': self.log_returns,
        }
