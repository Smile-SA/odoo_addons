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

from openerp.osv import orm, fields


class ProductProduct(orm.Model):
    _inherit = 'product.product'

    def _get_html_description(self, cr, uid, ids, name, arg, context=None):
        res = {}.fromkeys(ids, '')
        for product in self.browse(cr, uid, ids, context):
            overrides = dict(embed_stylesheet=False, doctitle_xform=False, output_encoding='unicode')
            output = publish_string(source=product.description, settings_overrides=overrides, writer=MyWriter())
            res[product.id] = output
        return res

    _columns = {
        'is_module': fields.boolean("Is module"),
        'repository_id': fields.many2one('ir.module.repository', "Repository", readonly=True),
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
    }

    _defaults = {
        'license': 'AGPL-3',
    }

    def create_or_update(self, cr, uid, vals_list, context=None):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        product_ids = self.search(cr, uid, [], context=context)
        product_infos = self.read(cr, uid, product_ids, ['name', 'variants'], context)
        product_ids_by_key = dict([((p['name'], p['variants']), p['id']) for p in product_infos])
        product_tmpl_obj = self.pool.get('product.template')
        product_tmpl_ids = product_tmpl_obj.search(cr, uid, [], context=context)
        product_tmpl_infos = product_tmpl_obj.read(cr, uid, product_ids, ['name'], context)
        product_tmpl_ids_by_key = dict([(p['name'], p['id']) for p in product_tmpl_infos])
        for vals in vals_list:
            for key in vals.keys():
                if key not in self._columns and key not in product_tmpl_obj._columns:
                    del vals[key]
            pkey = (vals['name'], vals.get('variants', ''))
            if pkey in product_ids_by_key:
                self.write(cr, uid, product_ids_by_key[pkey], vals, context)
            else:
                tkey = vals['name']
                if tkey in product_tmpl_ids_by_key:
                    vals['product_tmpl_id'] = product_tmpl_ids_by_key[tkey]
                    del vals['name']
                self.create(cr, uid, vals, context)
        return True
