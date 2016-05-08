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

import time

from openerp import api, fields, models, _
from openerp.exceptions import UserError
from openerp.modules.registry import Registry
from openerp.tools.safe_eval import safe_eval as eval

from openerp.addons.smile_log.tools import SmileDBLogger
from openerp.addons.smile_impex.models.impex import state_cleaner

from ..tools import with_impex_cursor


class IrModelExportTemplate(models.Model):
    _name = 'ir.model.export.template'
    _description = 'Export Template'
    _inherit = 'ir.model.impex.template'

    export_ids = fields.One2many('ir.model.export', 'export_tmpl_id', 'Exports', readonly=True, copy=False)
    log_ids = fields.One2many('smile.log', 'res_id', 'Logs', domain=[('model_name', '=', 'ir.model.export.template')],
                              readonly=True, copy=False)

    client_action_id = fields.Many2one('ir.values', 'Client Action', copy=False)
    filter_type = fields.Selection([('domain', 'Domain'), ('method', 'Method')], required=True, default='domain')
    filter_domain = fields.Text(default='[]', help="Available variables: context, time, user")
    filter_method = fields.Char(help="signature: @api.model + *args")
    limit = fields.Integer()
    max_offset = fields.Integer()
    order = fields.Char('Order by')
    unique = fields.Boolean(help="If unique, each record is exported only once")
    force_execute_action = fields.Boolean('Force Action Execution', help="Even if there are no record to export")
    do_not_store_record_ids = fields.Boolean('Do not store exported records',
                                             help="If checked, export regeneration will not be possible")

    @api.one
    @api.constrains('unique', 'do_not_store_record_ids')
    def _check_export_template_config(self):
        if self.unique and self.do_not_store_record_ids:
            raise UserError(_('Exported records storing is required if export must be unique'))

    def _get_cron_vals(self, **kwargs):
        vals = super(IrModelExportTemplate, self)._get_cron_vals(**kwargs)
        vals['function'] = 'create_export'
        return vals

    def _get_server_action_vals(self, model_id, **kwargs):
        vals = super(IrModelExportTemplate, self)._get_server_action_vals(model_id, **kwargs)
        if vals:
            vals['code'] = "self.pool.get('ir.model.export.template').create_export(cr, uid, %d, context)" % (self.id,)
        return vals

    def _get_client_action_vals(self, **kwargs):
        vals = {
            'name': self.name,
            'model_id': self.model_id.id,
            'model': self.model_id.model,
            'key2': 'client_action_multi',
            'value': 'ir.actions.server,%d' % self.server_action_id.id,
        }
        vals.update(kwargs)
        return vals

    @api.one
    def create_client_action(self, **kwargs):
        if not self.client_action_id:
            if not self.server_action_id:
                self.create_server_action()
            vals = self._get_client_action_vals(**kwargs)
            self.client_action_id = self.env['ir.values'].create(vals)
        return True

    @api.one
    def unlink_client_action(self):
        if self.client_action_id:
            self.client_action_id.unlink()
            if self.server_action_id:
                self.server_action_id.unlink()
        return True

    def _get_eval_context(self):
        return {'context': self._context, 'time': time, 'user': self.env.user}

    def _get_res_ids(self, *args):
        model_obj = self.env[self.model_id.model]
        if self._context.get('original_cr'):
            model_obj = model_obj.with_env(self.env(cr=self._context['original_cr']))
        if self.filter_type == 'domain':
            domain = eval(self.filter_domain or '[]', self._get_eval_context())
            res_ids = set(model_obj.search(domain, order=self.order or '')._ids)
        else:  # elif self.filter_type == 'method':
            if not (self.filter_method and hasattr(model_obj, self.filter_method)):
                raise UserError(_("Can't find method: %s on object: %s") % (self.filter_method, self.model_id.model))
            res_ids = set(getattr(model_obj, self.filter_method)(*args))
        if 'active_ids' in self._context:
            res_ids &= set(self._context['active_ids'])
        if self.unique:
            res_ids -= set(sum([eval(export.record_ids) for export in self.export_ids], []))
        return list(res_ids)

    def _get_res_ids_offset(self, *args):
        """Get records and split them in groups in function of limit and max_offset"""
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

    @api.multi
    @with_impex_cursor()
    def create_export(self, *args):
        self._try_lock(_('Export already in progress'))
        try:
            export_recs = self._create_export(*args)
        except Exception, e:
            tmpl_logger = SmileDBLogger(self._cr.dbname, self._name, self.id, self._uid)
            tmpl_logger.error(repr(e))
            raise UserError(repr(e))
        else:
            res = export_recs.process()
            if self.do_not_store_record_ids:
                export_recs.write({'record_ids': ''})
            return res

    @api.multi
    def _create_export(self, *args):
        export_recs = self.env['ir.model.export'].browse()
        vals = self._get_export_vals(*args)
        for index, res_ids_offset in enumerate(self._get_res_ids_offset(*args)):
            vals['record_ids'] = res_ids_offset
            vals['record_count'] = len(res_ids_offset)
            vals['offset'] = index + 1
            export_recs |= export_recs.create(vals)
        return export_recs

    @api.multi
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


class IrModelExport(models.Model):
    _name = 'ir.model.export'
    _description = 'Export'
    _inherit = 'ir.model.impex'

    def __init__(self, pool, cr):
        super(IrModelExport, self).__init__(pool, cr)
        setattr(Registry, 'setup_models', state_cleaner(pool[self._name])(getattr(Registry, 'setup_models')))

    export_tmpl_id = fields.Many2one('ir.model.export.template', 'Template', readonly=True, required=True,
                                     ondelete='cascade', index=True)
    log_ids = fields.One2many('smile.log', 'res_id', 'Logs', readonly=True,
                              domain=[('model_name', '=', 'ir.model.export')])
    offset = fields.Integer()
    record_ids = fields.Text('Records', readonly=True, required=True, default='[]')
    record_count = fields.Integer('# Records')

    @api.multi
    def _execute(self):
        self.ensure_one()
        if not self.record_ids:
            raise UserError(_("You cannot regenerate this export because records to export didn't store"))
        record_ids = eval(self.record_ids)
        if record_ids or self.export_tmpl_id.force_execute_action:
            records = self.env[self.export_tmpl_id.model_id.model].browse(record_ids)
            if self.export_tmpl_id.method:
                if self._context.get('original_cr'):
                    new_env = self.env(cr=self._context['original_cr'])
                    records = records.with_env(new_env)
                args = eval(self.args or '[]')
                kwargs = eval(self.export_tmpl_id.method_args or '{}')
                return getattr(records, self.export_tmpl_id.method)(*args, **kwargs)
