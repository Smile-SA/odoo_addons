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

from openerp import api, fields
from openerp.models import Model

native_setup_fields = Model._setup_fields
native_fields_view_get = Model.fields_view_get


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
def _setup_fields(self):
    name = self._get_attachments_field_name()
    if name not in self._fields:
        new_field = fields.One2many('ir.attachment', string='Attachments',
                                    compute='_get_attachments', search='_search_attachments')
        setattr(type(self), name, new_field)
        self._add_field(name, new_field)
    native_setup_fields(self)


@api.v7
def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
    res = native_fields_view_get(self, cr, uid, view_id, view_type, context, toolbar, submenu)
    name = self._get_attachments_field_name()
    if view_type == 'search' and (name in self._fields):
        View = self.pool['ir.ui.view']
        arch_etree = etree.fromstring(res['arch'])
        element = etree.Element('field', name=name)
        arch_etree.insert(-1, element)
        res['arch'], res['fields'] = View.postprocess_and_fields(cr, uid, self._name, arch_etree, view_id, context=context)
    return res


@api.v8
def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    res = native_fields_view_get(self, view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    name = self._get_attachments_field_name()
    if view_type == 'search' and (name in self._fields):
        View = self.env['ir.ui.view']
        arch_etree = etree.fromstring(res['arch'])
        element = etree.Element('field', name=name)
        arch_etree.insert(-1, element)
        res['arch'], res['fields'] = View.postprocess_and_fields(self._name, arch_etree, view_id)
    return res

Model._get_attachments_field_name = _get_attachments_field_name
Model._setup_fields = _setup_fields
Model._get_attachments = _get_attachments
Model._search_attachments = _search_attachments
Model.fields_view_get = fields_view_get
