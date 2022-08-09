# -*- coding: utf-8 -*-
# (C) 2022 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from copy import deepcopy

from odoo import api, fields, models, _
from odoo.tools import safe_eval


MAPPING_FIELDS_SWAGGER = {
    'binary': ('string', 'binary'),
    'boolean': ('boolean', ''),
    'char': ('string', ''),
    'date': ('string', 'date'),
    'datetime': ('string', 'date-time'),
    'float': ('number', 'float'),
    'html': ('string', ''),
    'integer': ('integer', ''),
    'many2many': ('array', ''),
    'many2one': ('integer', ''),
    'many2one_reference': ('integer', ''),
    'monetary': ('number', 'float'),
    'one2many': ('array', ''),
    'reference': ('string', ''),
    'selection': ('array', ''),
    'text': ('string', ''),
}


LIMIT_MAX = 500


def _convert_field_type_to_swagger(ttype):
    type_swagger, format_swagger = 'string', ''
    if ttype in MAPPING_FIELDS_SWAGGER:
        type_swagger, format_swagger = MAPPING_FIELDS_SWAGGER.get(ttype)
    return type_swagger, format_swagger


def _format_definition_name(name):
    return name and name.replace(' ', '') or ''


class ApiRestPath(models.Model):
    _name = 'api.rest.path'
    _order = 'model_id'
    _rec_name = 'model_id'
    _description = "Api Rest Path"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    version_id = fields.Many2one(
        'api.rest.version', string='API Version', required=True,
        ondelete='cascade')
    model_id = fields.Many2one('ir.model', required=True, ondelete='cascade')
    model = fields.Char(related='model_id.model', readonly=True)
    method = fields.Selection([
        ('get', 'Read'),
        ('post', 'Create'),
        ('put', 'Update'),
        ('delete', 'Delete'),
        ('custom', 'Custom function')
    ], required=True)
    description = fields.Html()
    deprecated = fields.Boolean()
    tag_id = fields.Many2one('api.rest.tag', string='Tag', ondelete='set null')
    # Read
    filter_domain = fields.Char(default="[]")
    field_ids = fields.Many2many(
        'ir.model.fields', domain="[('model_id', '=', model_id)]",
        string='Fields')
    limit = fields.Integer(string='Limit of results', default=500)
    # Create / Update
    warning_required = fields.Boolean(
        compute='_compute_warning_required', compute_sudo=True)
    api_field_ids = fields.One2many(
        'api.rest.field', 'path_id', string='Fields', copy=True)
    update_domain = fields.Char(default="[]")
    # Unlink
    unlink_domain = fields.Char(default="[]")
    # Custom function
    function_apply_on_record = fields.Boolean()
    function_domain = fields.Char(default="[]")
    function = fields.Char()
    function_parameter_ids = fields.One2many(
        'api.rest.function.parameter', 'path_id', string='Parameters',
        copy=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name, version_id, method)',
         "Name, Version, Method must be unique!"),
    ]

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.field_ids = False
        self.api_field_ids = False

    def _compute_warning_required(self):
        warning_required = False
        if self.api_field_ids:
            model_required_fields = self.model_id.field_id.filtered(
                lambda f: f.required).mapped('name')
            api_required_fields = self.api_field_ids.filtered(
                lambda f: f.required).mapped('field_id.name')
            warning_required = \
                not all(elem in api_required_fields
                        for elem in model_required_fields)
        self.warning_required = warning_required

    def _update_values(self, values):
        if values.get('name'):
            values['name'] = values.get('name', '').replace(' ', '')

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default.update(name=_("%s (copy)") % (self.name or ''))
        return super(ApiRestPath, self).copy(default)

    @api.model
    def create(self, values):
        self._update_values(values)
        return super().create(values)

    def write(self, values):
        self._update_values(values)
        return super().write(values)

    def _generate_path(self, swagger_paths):
        self.ensure_one()
        # Default values
        values = {
            'tags': self.tag_id and [self.tag_id.name or ''] or [],
            'description': self.description or '',
            'deprecated': self.deprecated,
            'produces': ['application/json'],
            'responses': {
                '200': {
                    'description': 'OK',
                },
                '401': {
                    'description': 'Unauthorized',
                    'schema': {
                        '$ref': '#/definitions/ApiErrorResponse'
                    }
                },
                '403': {
                    'description': 'Forbidden',
                    'schema': {
                        '$ref': '#/definitions/ApiErrorResponse'
                    }
                },
                '404': {
                    'description': 'Not found',
                    'schema': {
                        '$ref': '#/definitions/ApiErrorResponse'
                    }
                },
                '500': {
                    'description': 'Internal server error',
                    'schema': {
                        '$ref': '#/definitions/ApiErrorResponse'
                    }
                }
            },
            'security': [{
                'api_key': [],
            }],
        }
        # Get
        if self.method == 'get':
            # Default dict path
            get_path = '/{}'.format(self.name)
            if get_path not in swagger_paths:
                swagger_paths.setdefault(get_path, {})
            get_one_path = '/{}/{}'.format(self.name, '{Id}')
            if get_one_path not in swagger_paths:
                swagger_paths.setdefault(get_one_path, {})
            # Read All elements
            definition_all = {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'results': {
                            'type': 'array',
                            'items': {
                                '$ref': '#/definitions/{}'.format(
                                    _format_definition_name(self.name)),
                            }
                        },
                        'total': {
                            'type': 'integer',
                        },
                        'offset': {
                            'type': 'integer',
                        },
                        'limit': {
                            'type': 'integer',
                        }
                    }
                }
            }
            values['responses']['200'].update(definition_all)
            values.update(parameters=self._get_parameters_all_elements())
            swagger_paths[get_path].update({
                'get': values,
            })
            # Read One element
            values_one = deepcopy(values)
            definition_one = {
                'schema': {
                    '$ref': '#/definitions/{}'.format(
                        _format_definition_name(self.name)),
                }
            }
            values_one['responses']['200'].update(definition_one)
            values_one.update(parameters=self._get_parameters_one_element())
            swagger_paths[get_one_path].update({
                'get': values_one,
            })
        # Post
        elif self.method == 'post' and self.api_field_ids:
            # Default dict path
            post_path = '/{}'.format(self.name)
            if post_path not in swagger_paths:
                swagger_paths.setdefault(post_path, {})
            # Create element
            definition = {
                'description': _('Identifier of the resource created.'),
                'schema': {
                    'type': 'integer',
                }
            }
            values['responses']['200'].update(definition)
            values.update(
                consumes=self._form_urlencoded_consumes(),
                parameters=self._post_parameters()
            )
            swagger_paths[post_path].update({
                'post': values,
            })
        # Put
        elif self.method == 'put' and self.api_field_ids:
            # Default dict path
            put_path = '/{}/{}'.format(self.name, '{Id}')
            if put_path not in swagger_paths:
                swagger_paths.setdefault(put_path, {})
            # Update element
            definition = {
                'description': _('Return a boolean if update is a success.'),
                'schema': {
                    'type': 'boolean',
                }
            }
            values['responses']['200'].update(definition)
            values.update(
                consumes=self._form_urlencoded_consumes(),
                parameters=self._put_parameters(),
            )
            swagger_paths[put_path].update({
                'put': values,
            })
        # Delete
        elif self.method == 'delete':
            # Default dict path
            delete_path = '/{}/{}'.format(self.name, '{Id}')
            if delete_path not in swagger_paths:
                swagger_paths.setdefault(delete_path, {})
            # Delete element
            definition = {
                'description': _('Return a boolean if delete is a success.'),
                'schema': {
                    'type': 'boolean',
                }
            }
            values['responses']['200'].update(definition)
            values.update(parameters=self._delete_parameters())
            swagger_paths[delete_path].update({
                'delete': values,
            })
        # Put Custom function
        elif self.method == 'custom':
            # Delete element
            values.update(
                consumes=self._form_urlencoded_consumes(),
                parameters=self._custom_parameters())
            route = '/{}/{}'.format(self.name, 'custom')
            if self.function_apply_on_record:
                route = '/{}/{}/{}'.format(self.name, 'custom', '{Id}')
            swagger_paths[route] = {
                'put': values,
            }
        return True

    def _generate_definition(self, swagger_definitions):
        self.ensure_one()
        definition_name = _format_definition_name(self.name)
        if self.method == 'get':
            swagger_definitions[definition_name] = {
                'type': 'object',
                'properties': self._get_definition_properties(),
            }
        # Add ApiErrorResponse
        swagger_definitions['ApiErrorResponse'] = {
            'type': 'object',
            'properties': {
                'code': {
                    'type': 'integer',
                    'description': _('Error code')
                },
                'error': {
                    'type': 'string',
                    'description': _('Name of error')
                },
                'description': {
                    'type': 'string',
                    'description': _('Description of the error')
                }
            }
        }
        return True

    # Fields
    def _id_parameter(self):
        self.ensure_one()
        return {
            'name': 'Id',
            'in': 'path',
            'description': 'ID',
            'required': True,
            'type': 'integer',
        }

    def _domain_parameter(self):
        self.ensure_one()
        return {
            'name': 'domain',
            'in': 'query',
            'description': '{} \n\n {}'.format(
                _('Search domain to read. ('
                  'Defaults to an empty domain '
                  'that will match all records) '
                  '<a href="https://www.odoo.com/documentation/14.0/'
                  'fr/developer/reference/addons/'
                  'orm.html#reference-orm-domains" '
                  'target="_blank">Documentation</a>'),
                _('Example: `[(\'name\', \'=\', \'Test\')]`')),
            'required': False,
            'type': 'string',
        }

    def _fields_parameter(self):
        self.ensure_one()
        return {
            'name': 'fields',
            'in': 'query',
            'description': '{} \n\n {}'.format(
                _('List of fields to read. (Defaults to all fields)'),
                _('Example: `[\'id\', \'name\']`')),
            'required': False,
            'type': 'string',
        }

    def _offset_parameter(self):
        self.ensure_one()
        return {
            'name': 'offset',
            'in': 'query',
            'description': _('Number of records to skip. (Defaults to 0)'),
            'required': False,
            'type': 'integer',
        }

    def _limit_parameter(self):
        self.ensure_one()
        return {
            'name': 'limit',
            'in': 'query',
            'default': self.limit,
            'description':
                _('Maximum number of records to return. {}').format(
                    _('(Maximum: {})').format(
                        self.limit) if self.limit else ''),
            'required': False,
            'type': 'integer',
        }

    def _order_parameter(self):
        self.ensure_one()
        return {
            'name': 'order',
            'in': 'query',
            'description': '{} \n\n {}'.format(
                _('Param to sort result. (Defaults to no sort) '
                  '\n Field name followed by the sort operator. '
                  '(asc or desc)'),
                _('Example: {}').format(
                    "`name asc` {} `name desc, id asc`".format(_('or')))),
            'required': False,
            'type': 'string',
        }

    def _context_parameter(self, type="query"):
        self.ensure_one()
        return {
            'name': 'context',
            'in': type,
            'description': '{} \n\n {}'.format(
                _('Specific context to method'),
                _('Example: `{"lang": "fr_FR"}`')),
            'type': 'string',
            'required': False,
        }

    # Get
    def _get_parameters_all_elements(self):
        self.ensure_one()
        return [
            self._domain_parameter(),
            self._fields_parameter(),
            self._offset_parameter(),
            self._limit_parameter(),
            self._order_parameter(),
            self._context_parameter()
        ]

    def _get_parameters_one_element(self):
        self.ensure_one()
        return [
            self._id_parameter(),
            self._fields_parameter(),
            self._context_parameter()
        ]

    def _search_treatment_kwargs(self, kwargs):
        self.ensure_one()
        # Limit
        limit = kwargs.get('limit', 0)
        max_limit = self.limit if self.limit else LIMIT_MAX
        kwargs['limit'] = \
            limit if (limit and limit <= max_limit) else max_limit
        domain = kwargs.get('domain', [])
        if self.filter_domain:
            domain += self._eval_domain(self.filter_domain)
        kwargs['domain'] = domain
        # Fields
        self._treatment_fields(kwargs)
        return kwargs

    def _read_treatment_kwargs(self, kwargs):
        self.ensure_one()
        # Fields
        self._treatment_fields(kwargs)
        return kwargs

    def _treatment_fields(self, kwargs):
        self.ensure_one()
        lists_fields = ['id'] + self.field_ids.mapped('name')
        old_fields = kwargs.get('fields', [])
        if old_fields:
            kwargs['fields'] = list(set(old_fields) & set(lists_fields))
        else:
            kwargs['fields'] = lists_fields
        return kwargs

    def _get_definition_properties(self):
        self.ensure_one()
        properties = {
            'id': {
                'type': 'integer'
            }
        }
        for field in self.field_ids:
            _type, _format = _convert_field_type_to_swagger(field.ttype)
            values = {
                'type': _type,
                'format': _format,
                'description': field.field_description or ''
            }
            self._update_values_ttype(field, values, definition=True)
            properties.update({field.name: values})
        return properties

    # Post
    def _post_parameters(self):
        self.ensure_one()
        return self._post_properties() + [
            self._context_parameter(type='formData'),
        ]

    def _post_properties(self):
        self.ensure_one()
        properties = []
        for api_field in self.api_field_ids.filtered(
                lambda f: not f.default_value):
            field_name = api_field.field_name
            _type, _format = _convert_field_type_to_swagger(
                api_field.field_id.ttype)
            values = {
                'in': 'formData',
                'name': field_name,
                'type': _type,
                'format': _format,
                'description': api_field.description or '',
                'required': api_field.required,
            }
            # Update values in terms of ttype
            self._update_values_ttype(api_field.field_id, values)
            properties.append(values)
        return properties

    def _post_treatment_values(self, post_values):
        self.ensure_one()
        # Remove fields unspecified
        new_values = post_values.copy()
        api_fields = self.api_field_ids.mapped('field_name')
        for field, value in post_values.items():
            if field not in api_fields:
                new_values.pop(field)
        # Add fields with default_value
        for field in self.api_field_ids.filtered(lambda f: f.default_value):
            new_values[field.field_name] = \
                safe_eval.safe_eval(field.default_value)
        # Convert bool
        fields_boolean = self.api_field_ids.filtered(
            lambda f: f.field_id.ttype == 'boolean').mapped('field_name')
        for field in fields_boolean:
            if field in post_values:
                new_values[field] = \
                    True if post_values.get(
                        field) in ['1', 'true', 'True'] else False
        # Convert many2many & one2many
        fields_many2many = self.api_field_ids.filtered(
            lambda f:
            f.field_id.ttype in['many2many', 'one2many']).mapped('field_name')
        for field in fields_many2many:
            if field in post_values:
                values = post_values.get(field)
                if isinstance(values, int):
                    values = [values]
                new_values[field] = values
        return new_values

    # Put
    def _put_parameters(self):
        self.ensure_one()
        parameters = [
            self._id_parameter(),
        ]
        return parameters + self._post_properties() + [
            self._context_parameter(type='formData'),
        ]

    # Delete
    def _delete_parameters(self):
        self.ensure_one()
        return [
            self._id_parameter(),
            self._context_parameter(type='formData'),
        ]

    # Put Custom function
    def _custom_parameters(self):
        self.ensure_one()
        parameters = self._custom_function_parameters() + [
            self._context_parameter(type='formData')
        ]
        if self.function_apply_on_record:
            parameters = [self._id_parameter()] + parameters
        return parameters

    def _custom_function_parameters(self):
        self.ensure_one()
        properties = []
        for function_parameter in self.function_parameter_ids.filtered(
                lambda f: not f.default_value):
            parameter_format = ''
            parameter_type = function_parameter.type
            if parameter_type == 'float':
                parameter_type = 'number'
                parameter_format = 'float'
            values = {
                'name': function_parameter.name,
                'in': 'formData',
                'description': function_parameter.description or '',
                'required': function_parameter.required,
                'type': parameter_type,
                'format': parameter_format,
            }
            if parameter_type == 'array':
                values.update(items={'type': 'string'})
            properties.append(values)
        return properties

    def _custom_treatment_values(self, post_values):
        def _real_type_python(type):
            return {
                'integer': int,
                'float': float,
                'boolean': bool,
                'string': str,
                'array': list,
                'object': dict,
            }.get(type)
        self.ensure_one()
        new_values = {}
        for function_parameter in self.function_parameter_ids:
            # Convert fields to real type python
            if function_parameter.name in post_values:
                value = post_values.get(function_parameter.name)
                python_type = _real_type_python(function_parameter.type)
                if not isinstance(value, python_type):
                    # Try to convert
                    try:
                        new_value = python_type(value)
                        new_values[function_parameter.name] = new_value
                    except Exception:
                        # Delete value if it's not possible to convert
                        pass
                else:
                    new_values[function_parameter.name] = value
            # Add fields with default_value
            if function_parameter.default_value:
                new_values[function_parameter.name] = \
                    safe_eval.safe_eval(function_parameter.default_value)
        return new_values

    # Others function
    def _form_urlencoded_consumes(self):
        return [
            'application/x-www-form-urlencoded'
        ]

    def _update_values_ttype(self, field, values, definition=False):
        # Manage field selection
        field_name = field.name
        if field.ttype == 'selection':
            if definition:
                values.update({'type': 'string'})
            else:
                selection_keys = \
                    list(dict(self.env[self.model].fields_get(
                        [field_name])[field_name]['selection']).keys())
                values.update({
                    'items': {
                        'type': 'string',
                        'enum': selection_keys,
                    }
                })
        # Manage many2many & one2many
        if field.ttype in ['many2many', 'one2many']:
            values.update({'items': {
                'type': 'integer',
            }})
        # Manage many2one
        if field.ttype == 'many2one':
            if definition:
                values.update({
                    'type': 'array',
                    'items': {
                        'type': 'string',
                    },
                    'description': '{} \n\n {}'.format(
                        _('Return list with 2 element, '
                          'first ID of ressource (integer), '
                          'second Name of ressource (string).'),
                        _('Example : `[1, \'Example\']`')),
                })
        # Manage dates
        if field.ttype == 'date':
            description = values.get('description', '')
            description += '\n\n {}'.format(_('Example: `YYYY-MM-DD`'))
            values.update({'description': description})
        if field.ttype == 'datetime':
            description = values.get('description', '')
            description += \
                '\n\n {}'.format(_('Example: `YYYY-MM-DD HH:MM:SS`'))
            values.update({'description': description})
        return values

    def _get_eval_context(self):
        """ Prepare the context used when evaluating python code
            :returns: dict -- evaluation context given to safe_eval
        """
        return {
            'datetime': safe_eval.datetime,
            'dateutil': safe_eval.dateutil,
            'time': safe_eval.time,
            'uid': self.env.uid,
            'user': self.env.user,
        }

    def _eval_domain(self, domain):
        self.ensure_one()
        return safe_eval.safe_eval(domain, self._get_eval_context())
