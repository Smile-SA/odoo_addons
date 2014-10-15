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

from os import path, walk

from openerp import api, models, fields
from openerp.tools.safe_eval import safe_eval as eval


class Branch(models.Model):
    _inherit = 'scm.repository.branch'

    product_ids = fields.One2many('product.product', 'branch_id', 'Modules', readonly=True)

    @api.multi
    def clone(self):
        res = super(Branch, self).clone()
        self.extract_modules()
        return res

    @api.multi
    def pull(self):
        res = super(Branch, self).pull()
        self.extract_modules()
        return res

    @api.multi
    def extract_modules(self):
        product_obj = self.env['product.product']
        for branch in self:
            modules = branch._extract_modules()
            product_obj.create_or_update(modules)
            branch.refresh()  # Useful in v8.0 ?
            if len(modules) > len(branch.product_ids):
                variants = [(m['branch_id'], m['name']) for m in modules]
                for p in branch.product_ids:
                    if (p.branch_id.id, p.name) not in variants:
                        p.active = False
        return True

    def _extract_modules(self):
        modules = []
        for oerp_file in Branch._get_oerp_files(path.join(self._parent_path, self.directory)):
            module_infos = Branch._get_module_infos(oerp_file)
            module_infos['branch_id'] = self.id
            module_infos['default_code'] = self.version_id.name
            modules.append(module_infos)
        return modules

    @staticmethod
    def _get_oerp_files(dirpath):
        oerp_files = []
        if path.isdir(dirpath):
            for root, dirs, files in walk(dirpath):
                for filename in ('__odoo__.py', '__openerp__.py', '__terp__.py'):
                    if filename in files:
                        oerp_files.append(path.join(root, filename))
        return oerp_files

    @staticmethod
    def _get_module_icon(modulepath):
        icon_path = path.join(modulepath, 'static', 'src', 'img', 'icon.png')
        if path.isfile(icon_path):
            with open(icon_path, 'rb') as icon_file:
                return icon_file.read().encode('base64')
        return False

    @staticmethod
    def _get_module_infos(filepath):
        openerp_infos = {}
        if path.isfile(filepath):
            with open(filepath) as openerp_file:
                openerp_infos.update(eval(openerp_file.read()))
            module_path = path.dirname(filepath)
            openerp_infos.update({
                'name': path.basename(module_path),
                'shortdesc': openerp_infos['name'],
                'image': Branch._get_module_icon(module_path),
                'active': True,
                'is_module': True,
            })
        return openerp_infos
