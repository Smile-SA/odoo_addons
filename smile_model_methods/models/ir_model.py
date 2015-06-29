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

from inspect import ismethod, getargspec

from openerp import api, fields, models

METHOD_TYPES = [
    ('public', 'Public'),
    ('protected', 'Protected'),
    ('private', 'Private'),
    ('special', 'Special'),
]


class IrModelMethods(models.Model):
    _name = 'ir.model.methods'
    _description = 'Model Method'
    _order = 'name'

    @api.one
    @api.depends('name')
    def _get_type(self):
        if not self.name.startswith('_'):
            self.mtype = 'public'
        elif self.name.startswith('__') and self.name.endswith('__'):
            self.mtype = 'special'
        elif self.name.startswith('__'):
            self.mtype = 'private'
        else:
            self.mtype = 'protected'

    @api.one
    @api.depends('model_id.model')
    def _get_model(self):
        self.model = self.model_id.model

    @api.one
    def _set_model(self):
        self.model_id = self.env['ir.model'].search([('model', '=', self.model)], limit=1) if self.model else False

    @api.one
    @api.depends('name', 'model')
    def _get_signature(self):
        if self.model not in self.env.registry.models:
            self.mapi = False
            self.signature = False
            return
        method_name = self.name
        method = getattr(self.env[self.model], self.name)
        while hasattr(method, 'origin'):  # _patch_method
            method = method.origin
        self.mapi = method._api.__name__ if hasattr(method, '_api') and method._api else False
        if self.mapi == 'v8':
            method = method._v7
        elif self.mapi and hasattr(method, '_orig'):
            method = method._orig
        args, vname, kwname, defaults = getargspec(method)
        if self.mapi in ('model', 'one', 'multi'):
            args = ['self', 'cr', 'uid'] + list(args[1:]) + ['context']
            defaults = list(defaults) + [None] if defaults else [None]
            if self.mapi == 'one':
                args.insert(3, 'id')
            if self.mapi == 'multi':
                args.insert(3, 'ids')
        margs = args or []
        if defaults:
            margs = args[:-len(defaults)]
        if vname:
            margs.append('*%s' % vname)
        if defaults:
            for k, v in zip(args[-len(defaults):], defaults):
                margs.append('%s=%s' % (k, "'%s'" % v if isinstance(v, basestring) else v))
        if kwname:
            margs.append('**%s' % kwname)
        if method_name in ['browse', 'read', '_get_xml_ids']:
            if method_name == 'browse':
                margs = ['self', 'cr', 'uid', 'ids', 'context=None']
                self.mapi = 'v7, v8'
            elif method_name == 'read':
                margs = ['self', 'cr', 'uid', 'ids', 'fields=None', 'context=None', "load='_classic_read'"]
                self.mapi = 'v7, v8'
            else:
                margs = ['self', 'cr', 'uid', 'ids']
        self.signature = ', '.join(margs)

    name = fields.Char(required=True, readonly=True)
    mtype = fields.Selection(METHOD_TYPES, 'Type', compute='_get_type', store=True)
    model_id = fields.Many2one('ir.model', 'Model', ondelete='cascade', readonly=True, index=True)
    model = fields.Char('Technical Name', compute='_get_model', inverse='_set_model', compute_sudo=True, store=True)
    signature = fields.Char(compute='_get_signature', store=True)
    mapi = fields.Char('API', compute='_get_signature', store=True)
    active = fields.Boolean(readonly=True, default=True)
    docstring = fields.Text('Description', readonly=True)

    @api.model
    def update_list(self, models=None):
        self = self.sudo()
        if not models:
            models = self.env['ir.model'].search([]).mapped('model')
        existing_methods = {}
        to_update = self._context.get('to_update')
        # TODO: add constraint unique method/model
        for existing_method in self.search([('model', 'in', models)]):
            existing_methods.setdefault(existing_method.model, []).append(existing_method.name)
        for model in models:
            obj = self.env[model]
            methods = [attr for attr in dir(obj) if ismethod(getattr(obj, attr))]
            # Deactivate methods not existing anymore
            methods_to_deactivate = set(existing_methods.get(model, [])) - set(methods)
            if methods_to_deactivate:
                self.search([('model', '=', model), ('name', 'in', methods_to_deactivate)]).write({'active': False})
            for method in methods:
                # Create new methods
                if method not in existing_methods.get(model, []):
                    self.create({'name': method, 'model': model, 'docstring': getattr(obj, method).__doc__ or ''})
                # update records
                elif to_update:
                    record = self.search([('model', '=', model), ('name', '=', method)], limit=1)
                    record.write({'name': method, 'model': model, 'docstring': getattr(obj, method).__doc__ or ''})
        return True
