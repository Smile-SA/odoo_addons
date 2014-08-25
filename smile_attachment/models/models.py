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

from lxml import etree

from openerp import api, fields, models

native__init__ = models.Model.__init__
native_fields_view_get = models.Model.fields_view_get


@api.one
@api.depends()
def _get_attachments(self):
    self.attachment_ids = False


def _search_attachments(self, operator, value):
    recs = self.env['ir.attachment'].search([('res_model', '=', self._name),
                                             '|', '|',
                                             ('description', operator, value),
                                             ('index_content', operator, value),
                                             ('datas_fname', operator, value)])
    return [('id', 'in', [rec.res_id for rec in recs])]


def new__init__(self, pool, cr):
    native__init__(self, pool, cr)
    name = 'attachment_ids'
    if name not in self._columns and name not in self._fields:
        field = fields.One2many('ir.attachment', 'res_id', 'Attachments', automatic=True,
                                compute='_get_attachments', search='_search_attachments')
        self._add_field(name, field)


def new_fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
    res = native_fields_view_get(self, cr, uid, view_id, view_type, context, toolbar, submenu)
    if view_type == 'search':
        View = self.pool['ir.ui.view']
        arch_etree = etree.fromstring(res['arch'])
        element = etree.Element('field', name='attachment_ids')
        arch_etree.insert(-1, element)
        res['arch'], res['fields'] = View.postprocess_and_fields(cr, uid, self._name, arch_etree, view_id, context=context)
    return res

models.Model.__init__ = new__init__
models.Model._get_attachments = _get_attachments
models.Model._search_attachments = _search_attachments
models.Model.fields_view_get = new_fields_view_get
