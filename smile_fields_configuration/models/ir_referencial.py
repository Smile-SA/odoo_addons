# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from ast import literal_eval

from odoo import fields, models, api, _
from odoo.tools.safe_eval import safe_eval


DEFAULT_PYTHON_CODE = """# Available variables:
#  - env: Odoo Environment on which the action is triggered
#  - record: record on which the action is triggered
#  - data: Current data for record
#  - object: Object is the result of the API Call
# To return an result, assign: result = {...}
# Examples:
# -> result = object.get('field1', '') # Simple mapping
# -> result = {'id': field_id} # Mapping for relation field\n\n\n\n"""


def convert_m2o(value):
    if isinstance(value, dict) and 'id' in value:
        return value.get('id')
    return value


def eval_proxies(proxies):
    try:
        proxies = safe_eval(proxies)
        if isinstance(proxies, dict):
            return proxies
        return None
    except Exception:
        return None


class IrReferencial(models.Model):
    _name = 'ir.referencial'
    _description = 'Referencial'

    name = fields.Char(required=True)
    description = fields.Text()
    url_auth = fields.Char()
    url_api = fields.Char()
    api_key = fields.Char()
    url_docs = fields.Char()
    proxies = fields.Char(string='Proxies API')
    proxies_auth = fields.Char(string='Proxies Auth')

    # Technical field to display error on wizard
    error_message = fields.Text(readonly=True)

    def get_referencial(self):
        self.ensure_one()
        return {
            'referencial_id': self.id,
            'url_api': self.url_api,
            'api_key': self.api_key,
            'proxies': eval_proxies(self.proxies),
            'proxies_auth': eval_proxies(self.proxies_auth),
        }

    def get_lines_referencial(
            self, referencial, autocomplete_record_data, autocomplete_model):
        ReferencialLine = self.env['ir.referencial.line'].sudo()
        lines_referencial = []
        for line in ReferencialLine.search([
            ('referencial_id', '=', referencial.id),
            ('model', '=', autocomplete_model),
        ]):
            if not line.domain or line.domain == '[]':
                lines_referencial.append(line.id)
            else:
                if autocomplete_record_data.get('__last_update'):
                    del autocomplete_record_data['__last_update']
                fake_object = self.env[autocomplete_model].sudo().new(
                    autocomplete_record_data).filtered_domain(
                    literal_eval(line.domain))
                if fake_object:
                    lines_referencial.append(line.id)
        return lines_referencial

    def get_default_changes(self, referencial_id, convert_for):
        return {}

    @api.model
    def convert_fields_referencial(self, item, referencial_id, data, model,
                                   convert_for='autocomplete'):
        changes = self.get_default_changes(referencial_id, convert_for)
        errors = []
        ReferencialLine = self.env['ir.referencial.line'].sudo()
        referencial = self.env['ir.referencial'].sudo().browse(referencial_id)
        lines_referencial = \
            self.get_lines_referencial(referencial, data, model)
        lines_is_referencial_key = []
        for line in ReferencialLine.browse(lines_referencial):
            eval_context = {
                'env': self.with_context(
                    convert_fields_referencial=True).env, 'record': line,
                'data': data, 'model': model, 'object': item,
            }
            field_name = line.configuration_id.field_id.name
            field_model = line.configuration_id.field_id.model
            field_type = line.configuration_id.field_id.ttype
            field_description = \
                line.configuration_id.field_id.field_description
            try:
                safe_eval(
                    line.code.strip(), eval_context, mode="exec", nocopy=True)
            except Exception as e:
                errors.append(_('{} ({}): {} \n'.format(
                    field_description, field_model, e)))
                continue
            result = eval_context.get('result', False)
            if field_type == 'boolean' or result:
                # Treatment by mode
                if convert_for in ['create', 'write']:
                    if field_type == 'many2one' and result:
                        result = convert_m2o(result)
                if convert_for == 'autocomplete':
                    if line.is_referencial_key:
                        lines_is_referencial_key.append(line)
                # Update value to changes
                changes.update({field_name: result})
        if lines_is_referencial_key and changes and \
                convert_for == 'autocomplete':
            domain = []
            for line in lines_is_referencial_key:
                field_name = line.configuration_id.field_id.name
                field_type = line.configuration_id.field_id.ttype
                if field_name in changes:
                    value = changes[field_name]
                    if field_type == 'many2one' and value:
                        value = convert_m2o(value)
                domain += [(field_name, '=', value)]
            if domain:
                find_exist_record = \
                    self.env[model].sudo().search(domain, limit=1)
                if find_exist_record:
                    if getattr(
                            find_exist_record, '_get_action_redirect'):
                        action_redirect = \
                            find_exist_record._get_action_redirect()
                        if action_redirect:
                            action_redirect['res_id'] = find_exist_record.id
                            return changes, [], action_redirect
        return changes, errors, False

    def _format_error_message(self, errors):
        error_message = '\n'
        for error in errors:
            error_message += '- {} \n'.format(error)
        return error_message

    @api.model
    def open_wizard_warning_error(self, errors):
        return {
            'name': _('Synchronization with errors'),
            'res_model': 'ir.referencial',
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_error_message': self._format_error_message(errors),
                'no_customize': True,
            },
            'views': [(self.env.ref(
                'smile_fields_configuration.'
                'ir_referencial_view_form_warning_error').id, 'form')],
        }


class IrReferencialLine(models.Model):
    _name = 'ir.referencial.line'
    _description = 'Referencial line'
    _rec_name = 'referencial_id'

    configuration_id = fields.Many2one(
        'ir.model.fields.configuration', required=True, ondelete='cascade')
    referencial_id = fields.Many2one(
        'ir.referencial', required=True, ondelete='cascade')
    model = fields.Char(
        related='configuration_id.model', store=True, readonly=True)
    domain = fields.Char(default='[]')
    technical_model_name = fields.Char()
    technical_field_name = fields.Char()
    is_referencial_key = fields.Boolean(string='Key in the ref')
    code = fields.Text(string='Python Code', default=DEFAULT_PYTHON_CODE)
