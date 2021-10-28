# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

# flake8: noqa
# do not check flake8 because of F811 error
from lxml import etree

from odoo import api, fields, models


class Base(models.AbstractModel):
    _inherit = "base"

    def _get_attachments_field_name(self):
        name = 'attachment_ids'
        if self._inherits:
            name = 'attachment_%s_ids' % self._table
        return name

    @api.depends()
    def _get_attachments(self):
        for record in self:
            name = record._get_attachments_field_name()
            setattr(record, name, False)

    def _search_attachments(self, operator, value):
        domain = [
            ('res_model', '=', self._name),
            '|',
            ('description', operator, value),
            ('name', operator, value),
        ]
        if 'ir.module.module' in self.env.registry.models and \
                self.env['ir.module.module'].search([
                    ('name', '=', 'attachment_indexation'),
                    ('state', 'in', ('to upgrade', 'installed')),
                ], limit=1):
            domain = domain[:2] + [
                '|', ('index_content', operator, value)] + domain[2:]
        recs = self.env['ir.attachment'].search(domain)
        return [('id', 'in', [rec.res_id for rec in recs])]

    @api.model
    def _setup_fields(self):
        name = self._get_attachments_field_name()
        if name not in self._fields and \
                not self._abstract and not self._transient:
            new_field = fields.One2many(
                'ir.attachment', string='Attachments',
                compute='_get_attachments', search='_search_attachments')
            setattr(type(self), name, new_field)
            self._add_field(name, new_field)
        super(Base, self)._setup_fields()

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super(Base, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if view_type == 'search' and \
                hasattr(self, '_get_attachments_field_name'):
            name = self._get_attachments_field_name()
            if name in self._fields:
                View = self.env['ir.ui.view']
                arch_etree = etree.fromstring(res['arch'])
                element = etree.Element('field', name=name)
                arch_etree.insert(-1, element)
                res['arch'], res['fields'] = View.postprocess_and_fields(arch_etree, self._name)
        return res

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(Base, self).fields_get(allfields, attributes)
        if hasattr(self, '_get_attachments_field_name') and \
                (not allfields or 'attachment_ids' in allfields):
            name = self._get_attachments_field_name()
            if name in res:
                res[name]['string'] = self.env['ir.translation']._get_source(
                    'ir.model.fields,field_description', 'model',
                    self.env.lang, 'Attachments')
        return res
