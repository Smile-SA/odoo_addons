# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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

from docutils.core import publish_string
from os import path
from subprocess import os
import uuid
from zipfile import ZipFile

from openerp import api, models, fields, _
from openerp.addons.base.module.module import MyWriter

from openerp.addons.smile_scm.models.tools import cd
from tools import zipdir


class ProductCategory(models.Model):
    _inherit = 'product.category'

    @api.model
    def get_db_id(self, name):
        if not name:
            return self.env.ref('smile_module_repository.product_category_unknown').id
        categories = self.search([('name', '=', name)], limit=1)
        if categories:
            return categories[0].id
        parent_id = self.env.ref('smile_module_repository.product_category_modules').id
        return self.create({'name': name, 'parent_id': parent_id}).id


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_module = fields.Boolean()

    @api.model
    def _get_all_products(self):
        product_tmpl_infos = self.search_read([], ['name'])
        return dict([(p['name'], p['id']) for p in product_tmpl_infos])


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.one
    @api.depends('description')
    def _get_html_description(self):
        overrides = dict(embed_stylesheet=False, doctitle_xform=False,
                         output_encoding='unicode', xml_declaration=False)
        self.description_html = publish_string(source=self.description or '',
                                               settings_overrides=overrides,
                                               writer=MyWriter())

    @api.one
    @api.depends('branch_id.repository_id', 'branch_id.tag_ids')
    def _get_tags(self):
        self.tag_ids = self.branch_id and self.branch_id.tag_ids

    branch_id = fields.Many2one('scm.repository.branch', "Branch", readonly=True, ondelete="cascade")
    shortdesc = fields.Char('Module Name', size=64, readonly=True, translate=True)
    version = fields.Char('Latest Version', size=64, readonly=True)
    author = fields.Char(size=128, readonly=True)
    website = fields.Char(size=256, readonly=True)
    depends = fields.Text("Dependencies", readonly=True)
    license = fields.Selection([
        ('GPL-2', 'GPL Version 2'),
        ('GPL-2 or any later version', 'GPL-2 or later version'),
        ('GPL-3', 'GPL Version 3'),
        ('GPL-3 or any later version', 'GPL-3 or later version'),
        ('AGPL-3', 'Affero GPL-3'),
        ('Other OSI approved licence', 'Other OSI Approved Licence'),
        ('Other proprietary', 'Other Proprietary')
    ], string='License', readonly=True, default='AGPL-3')
    description_html = fields.Html("Description HTML", compute="_get_html_description")
    vcs_id = fields.Many2one('scm.vcs', 'Version Control System', related='branch_id.vcs_id')
    version_id = fields.Many2one('scm.version', 'Odoo Version', related='branch_id.version_id')
    tag_ids = fields.Many2many('scm.repository.tag', string='Tags', compute='_get_tags')
    zipfile = fields.Binary('Download zip', readonly=True)
    zipfilename = fields.Char('Zip file name', size=128, readonly=True)

    @api.model
    def _get_all_products(self):
        product_infos = self.search_read([], ['name', 'branch_id'])
        return dict([((p['name'], p['branch_id']), p['id']) for p in product_infos])

    @api.model
    def create_or_update(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        product_ids_by_key = self._get_all_products()
        product_categ_obj = self.env['product.category']
        product_tmpl_obj = self.env['product.template']
        product_tmpl_ids_by_key = product_tmpl_obj._get_all_products()
        product_fields = self._columns.keys() + self._fields.keys()
        product_tmpl_fields = product_tmpl_obj._columns.keys() + product_tmpl_obj._fields.keys()
        for vals in vals_list:
            vals['categ_id'] = product_categ_obj.get_db_id(vals.get('category'))
            for key in vals.keys():
                if key not in product_fields and key not in product_tmpl_fields:
                    del vals[key]
            pkey = (vals['name'], vals['branch_id'])
            if pkey in product_ids_by_key:
                self.browse(product_ids_by_key[pkey]).write(vals)
            else:
                tkey = vals['name']
                if tkey in product_tmpl_ids_by_key:
                    vals['product_tmpl_id'] = product_tmpl_ids_by_key[tkey]
                    del vals['name']
                self.create(vals)
        return True

    @api.multi
    def name_get(self):
        res = dict(super(ProductProduct, self).name_get())
        for product in self:
            if product.is_module:
                res[product.id] = '[%s] %s - %s' % (product.default_code, product.name, product.author)
        return res.items()

    @api.multi
    def get_zipfile(self, cr, uid, ids, context=None):
        assert len(self) == 1, 'ids must be a list with only one item!'
        zfilecontent = ''
        zfilename = '%s_%s.zip' % (self.name, uuid.uuid4())
        with cd(path.join(self.branch_id._parent_path, self.branch_id.directory)):
            dirpath = path.join(os.getcwd(), self.name)
            if path.isdir(dirpath):
                with ZipFile(zfilename, 'w') as zfile:
                    zipdir(path.relpath(dirpath), zfile)
                with open(zfilename, 'rb') as zfile:
                    zfilecontent = zfile.read().encode('base64')
                self.write({'zipfile': zfilecontent, 'zipfilename': '%s.zip' % self.name})
        return {
            'name': _('Download zip'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.product',
            'res_id': self.id,
            'view_id': self.env.ref('smile_module_repository.view_product_product_form2').id,
            'target': 'new',
            'context': self._context,
        }
