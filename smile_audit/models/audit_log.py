# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from dateutil import tz

from openerp import api, fields, models, _
from openerp.exceptions import UserError
from openerp.tools.safe_eval import safe_eval as eval


class AuditLog(models.Model):
    _name = 'audit.log'
    _description = 'Audit Log'
    _order = 'create_date desc, id desc'

    name = fields.Char('Resource Name', size=256, compute='_get_name')
    create_date = fields.Datetime('Date', readonly=True)
    user_id = fields.Many2one('res.users', 'User', required=True, readonly=True)
    model_id = fields.Many2one('ir.model', 'Model', required=True, readonly=True)
    model = fields.Char(related='model_id.model', store=True, readonly=True, index=True)
    res_id = fields.Integer('Resource Id', readonly=True)
    method = fields.Char('Method', size=64, readonly=True)
    data = fields.Text('Data', readonly=True)
    data_html = fields.Html('HTML Data', readonly=True, compute='_render_html')

    @api.one
    def _get_name(self):
        if self.model_id and self.res_id:
            record = self.env[self.model_id.model].browse(self.res_id).exists()
            if record:
                self.name = record.display_name
            else:
                data = eval(self.data or '{}')
                rec_name = self.env[self.model_id.model]._rec_name
                if rec_name in data['new']:
                    self.name = data['new'][rec_name]
                elif rec_name in data['old']:
                    self.name = data['old'][rec_name]
                else:
                    self.name = 'id=%s' % self.res_id
        else:
            self.name = ''

    @api.multi
    def _format_value(self, field, value):
        self.ensure_one()
        if not value and field.type not in ('boolean', 'integer', 'float'):
            return ''
        if field.type == 'selection':
            selection = field.selection
            if callable(selection):
                selection = selection(self.env[self.model_id.model])
            return dict(selection).get(value, value)
        if field.type == 'many2one' and value:
            return self.env[field.comodel_name].browse(value).exists().display_name or value
        if field.type == 'reference' and value:
            res_model, res_id = value.split(',')
            return self.env[res_model].browse(int(res_id)).exists().display_name or value
        if field.type in ('one2many', 'many2many') and value:
            return ', '.join([self.env[field.comodel_name].browse(rec_id).exists().display_name or str(rec_id)
                              for rec_id in value])
        if field.type == 'binary' and value:
            return '&lt;binary data&gt;'
        if field.type == 'datetime':
            from_tz = tz.tzutc()
            to_tz = tz.gettz(self.env.user.tz)
            datetime_wo_tz = fields.Datetime.from_string(value)
            datetime_with_tz = datetime_wo_tz.replace(tzinfo=from_tz)
            return fields.Datetime.to_string(datetime_with_tz.astimezone(to_tz))
        return value

    @api.multi
    def _get_content(self):
        self.ensure_one()
        content = []
        data = eval(self.data or '{}')
        model_obj = self.env[self.model_id.model]
        for fname in set(data['new'].keys() + data['old'].keys()):
            field = model_obj._fields.get(fname) or model_obj._inherit_fields.get(fname)
            old_value = self._format_value(field, data['old'].get(fname, ''))
            new_value = self._format_value(field, data['new'].get(fname, ''))
            if old_value != new_value:
                label = field.get_description(self.env)['string']
                content.append((label, old_value, new_value))
        return content

    @api.one
    def _render_html(self):
        thead = ''
        for head in (_('Field'), _('Old value'), _('New value')):
            thead += '<th>%s</th>' % head
        thead = '<thead><tr class="oe_list_header_columns">%s</tr></thead>' % thead
        tbody = ''
        for line in self._get_content():
            row = ''
            for item in line:
                row += '<td>%s</td>' % item
            tbody += '<tr>%s</tr>' % row
        tbody = '<tbody>%s</tbody>' % tbody
        self.data_html = '<table class="oe_list_content">%s%s</table>' % (thead, tbody)

    @api.multi
    def unlink(self):
        raise UserError(_('You cannot remove audit logs!'))

    @api.multi
    def display_history_revision(self):
        self.ensure_one()
        self._cr.execute('SELECT create_date FROM %s WHERE id = %%s' % self._table, (self.id,))
        create_date = self._cr.dictfetchall()[0]['create_date']
        return {
            'name': self.model_id.name,
            'type': 'ir.actions.act_window',
            'res_model': self.model,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,  # TODO: get it
            'res_id': self.res_id,
            'context': {'history_revision': create_date},
        }
