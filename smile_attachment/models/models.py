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

# flake8: noqa
# do not check flake8 because of F811 error
from lxml import etree

from odoo import api, fields
from odoo.models import BaseModel, Model

native_setup_fields = Model._setup_fields
native_fields_get = BaseModel.fields_get
native_fields_view_get = BaseModel.fields_view_get


def _get_attachments_field_name(self):
    name = 'attachment_ids'
    if self._inherits:
        name = 'attachment_%s_ids' % self._table
    return name


@api.one
@api.depends()
def _get_attachments(self):
    name = self._get_attachments_field_name()
    setattr(self, name, False)


def _search_attachments(self, operator, value):
    domain = [
        ('res_model', '=', self._name),
        '|', ('description', operator, value),
        ('datas_fname', operator, value),
    ]
    if 'ir.module.module' in self.env.registry.models and \
            self.env['ir.module.module'].search([('name', '=', 'document'),
                                                 ('state', 'in', ('to upgrade', 'installed'))], limit=1):
        domain = domain[:2] + ['|', ('index_content', operator, value)] + domain[2:]
    recs = self.env['ir.attachment'].search(domain)
    return [('id', 'in', [rec.res_id for rec in recs])]


@api.model
def _setup_fields(self, partial):
    name = self._get_attachments_field_name()
    if name not in self._fields:
        new_field = fields.One2many('ir.attachment', string='Attachments',
                                    compute='_get_attachments', search='_search_attachments')
        setattr(type(self), name, new_field)
        self._add_field(name, new_field)
    native_setup_fields(self, partial)


@api.model
def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    res = native_fields_view_get(self, view_id=view_id, view_type=view_type,
                                 toolbar=toolbar, submenu=submenu)
    if view_type == 'search' and hasattr(self, '_get_attachments_field_name'):
        name = self._get_attachments_field_name()
        if name in self._fields:
            View = self.env['ir.ui.view']
            arch_etree = etree.fromstring(res['arch'])
            element = etree.Element('field', name=name)
            arch_etree.insert(-1, element)
            res['arch'], res['fields'] = View.postprocess_and_fields(self._name, arch_etree, view_id)
    return res


@api.model
def fields_get(self, allfields=None, write_access=True, attributes=None):
    res = native_fields_get(self, allfields, attributes)
    if hasattr(self, '_get_attachments_field_name') and \
            (not allfields or 'attachment_ids' in allfields):
        name = self._get_attachments_field_name()
        res[name]['string'] = self.env['ir.translation']._get_source(
            'ir.model.fields,field_description', 'model', self.env.lang,
            'Attachments')
    return res

Model._get_attachments_field_name = _get_attachments_field_name
Model._setup_fields = _setup_fields
Model._get_attachments = _get_attachments
Model._search_attachments = _search_attachments
BaseModel.fields_get = fields_get
BaseModel.fields_view_get = fields_view_get
