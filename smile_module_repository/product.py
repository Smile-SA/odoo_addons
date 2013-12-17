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

from openerp.addons.base.module.module import MyWriter
from openerp.osv import orm, fields
from openerp.tools.translate import _

from tools import cd, zipdir


class ProductCategory(orm.Model):
    _inherit = 'product.category'

    def get_db_id(self, cr, uid, name, context=None):
        if not name:
            return False
        ids = self.search(cr, uid, [('name', '=', name)], limit=1, context=context)
        if ids:
            return ids[0]
        parent_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'smile_module_repository', 'product_category_modules')[1]
        return self.create(cr, uid, {'name': name, 'parent_id': parent_id}, context)


class ProductTemplate(orm.Model):
    _inherit = 'product.template'

    _columns = {
        'is_module': fields.boolean("Is module"),
    }

    def _get_all_products(self, cr, uid, context=None):
        product_tmpl_ids = self.search(cr, uid, [], context=context)
        product_tmpl_infos = self.read(cr, uid, product_tmpl_ids, ['name'], context)
        return dict([(p['name'], p['id']) for p in product_tmpl_infos])


class ProductProduct(orm.Model):
    _inherit = 'product.product'

    def _get_html_description(self, cr, uid, ids, name, arg, context=None):
        res = {}.fromkeys(ids, '')
        for product in self.browse(cr, uid, ids, context):
            overrides = dict(embed_stylesheet=False, doctitle_xform=False, output_encoding='unicode')
            output = publish_string(source=product.description, settings_overrides=overrides, writer=MyWriter())
            res[product.id] = output
        return res

    def _get_product_ids_from_repositories(self, cr, uid, ids, context=None):
        context = context and context.copy() or {}
        context['active_test'] = False
        return self.pool.get('product.product').search(cr, uid, [('repository_id', 'in', ids)], context=context)

    def _get_tag_ids(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for product in self.browse(cr, uid, ids, context):
            res[product.id] = product.repository_id and [tag.id for tag in product.repository_id.tag_ids] or []
        return res

    _columns = {
        'repository_id': fields.many2one('ir.module.repository', "Repository", readonly=True, ondelete="cascade"),
        'shortdesc': fields.char('Module Name', size=64, readonly=True, translate=True),
        'version': fields.char('Latest Version', size=64, readonly=True),
        'author': fields.char("Author", size=128, readonly=True),
        'website': fields.char("Website", size=256, readonly=True),
        'depends': fields.text("Dependencies", readonly=True),
        'license': fields.selection([
            ('GPL-2', 'GPL Version 2'),
            ('GPL-2 or any later version', 'GPL-2 or later version'),
            ('GPL-3', 'GPL Version 3'),
            ('GPL-3 or any later version', 'GPL-3 or later version'),
            ('AGPL-3', 'Affero GPL-3'),
            ('Other OSI approved licence', 'Other OSI Approved Licence'),
            ('Other proprietary', 'Other Proprietary')
        ], string='License', readonly=True),
        'description_html': fields.function(_get_html_description, method=True, type='html', string='Description HTML'),
        'vcs_id': fields.related('repository_id', 'vcs_id', type='many2one', relation='ir.module.vcs', string='Version Control System', store={
            'product.product': (lambda self, cr, uid, ids, context=None: ids, ['repository_id'], 5),
            'ir.module.repository': (_get_product_ids_from_repositories, ['vcs_id'], 5),
        }),
        'version_id': fields.related('repository_id', 'version_id', type='many2one', relation='ir.module.version', string='OpenERP Version', store={
            'product.product': (lambda self, cr, uid, ids, context=None: ids, ['repository_id'], 5),
            'ir.module.repository': (_get_product_ids_from_repositories, ['version_id'], 5),
        }),
        'tag_ids': fields.function(_get_tag_ids, method=True, type='many2many', relation='ir.module.repository.tag', string="Tags"),
        'zipfile': fields.binary('Download zip', readonly=True),
        'zipfilename': fields.char('Zip file name', size=128, readonly=True),
    }

    _defaults = {
        'license': 'AGPL-3',
    }

    def _get_all_products(self, cr, uid, context=None):
        product_ids = self.search(cr, uid, [], context=context)
        product_infos = self.read(cr, uid, product_ids, ['name', 'repository_id'], context, '_classic_write')
        return dict([((p['name'], p['repository_id']), p['id']) for p in product_infos])

    def create_or_update(self, cr, uid, vals_list, context=None):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        product_ids_by_key = self._get_all_products(cr, uid, context)
        product_tmpl_obj = self.pool.get('product.template')
        product_tmpl_ids_by_key = product_tmpl_obj._get_all_products(cr, uid, context)
        for vals in vals_list:
            vals['categ_id'] = self.pool.get('product.category').get_db_id(cr, uid, vals.get('category'), context)
            for key in vals.keys():
                if key not in self._columns and key not in product_tmpl_obj._columns:
                    del vals[key]
            pkey = (vals['name'], vals['repository_id'])
            if pkey in product_ids_by_key:
                self.write(cr, uid, product_ids_by_key[pkey], vals, context)
            else:
                tkey = vals['name']
                if tkey in product_tmpl_ids_by_key:
                    vals['product_tmpl_id'] = product_tmpl_ids_by_key[tkey]
                    del vals['name']
                self.create(cr, uid, vals, context)
        return True

    def name_get(self, cr, uid, ids, context=None):
        res = dict(super(ProductProduct, self).name_get(cr, uid, ids, context))
        if isinstance(ids, (int, long)):
            ids = [ids]
        for product in self.browse(cr, uid, ids, context):
            if product.is_module:
                res[product.id] = '[%s] %s - %s' % (product.default_code, product.name, product.author)
        return res.items()

    def get_zipfile(self, cr, uid, ids, context=None):
        zfilecontent = ''
        if isinstance(ids, (int, long)):
            ids = [ids]
        product = self.browse(cr, uid, ids[0], context)
        zfilename = '%s_%s.zip' % (product.name, uuid.uuid4())
        with cd(path.join(product.repository_id._parent_path, product.repository_id.relpath)):
            dirpath = path.join(os.getcwd(), product.name)
            if path.isdir(dirpath):
                with ZipFile(zfilename, 'w') as zfile:
                    zipdir(path.relpath(dirpath), zfile)
                with open(zfilename, 'rb') as zfile:
                    zfilecontent = zfile.read().encode('base64')
                product.write({'zipfile': zfilecontent, 'zipfilename': '%s.zip' % product.name})
        return {
            'name': _('Download zip'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.product',
            'res_id': product.id,
            'view_id': self.pool.get('ir.model.data').get_object_reference(cr, uid, 'smile_module_repository',
                                                                           'view_product_product_form2')[1],
            'target': 'new',
            'context': context,
        }
