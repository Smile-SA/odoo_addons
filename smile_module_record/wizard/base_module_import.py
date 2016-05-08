# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Smile (<http://www.smile.fr>).
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

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from io import BytesIO
import logging
import os.path
import re
import zipfile

from openerp import api, fields, models, modules, _
from openerp.exceptions import UserError

_logger = logging.getLogger(__package__)


class BaseModuleImport(models.TransientModel):
    _name = 'base.module.import'
    _description = "Base Module Import"

    module_name = fields.Char(required=True, help="Technical name")
    file = fields.Binary(required=True)

    @api.one
    @api.constrains('module_name')
    def _check_module_name(self):
        invalid_characters = re.findall(r'[^A-Za-z0-9_\-]', self.module_name)
        if invalid_characters:
            raise UserError(_("Invalid characters in module name: '%s'") % "', '".join(invalid_characters))
        if self.env['ir.module.module'].search_count([('name', '=', self.module_name)]):
            raise UserError(_("The module '%s' already exists") % self.module_name)

    @api.one
    @api.constrains('file')
    def _check_zipfile(self):
        filecontent = self._get_file_content()
        module_file = BytesIO()
        module_file.write(filecontent)
        if not zipfile.is_zipfile(module_file):
            raise UserError(_('File is not a zip file!'))

    @api.multi
    def _get_file_content(self):
        self.ensure_one()
        return self.file.decode('base64')

    @api.multi
    def _get_module_path(self):
        self.ensure_one()
        module_path = modules.get_module_path('', downloaded=True, display_warning=False)
        return os.path.join(module_path, self.module_name)

    @api.multi
    def download(self):
        filecontent = self._get_file_content()
        module_path = self._get_module_path()
        zipfile.ZipFile(StringIO(filecontent)).extractall(module_path)
        return self.env['ir.module.module'].sudo().update_list()

    @api.multi
    def install(self):
        self.ensure_one()
        modules = self.env['ir.module.module'].sudo().search([('name', '=', self.module_name)])
        return modules.button_immediate_install()

    @api.multi
    def download_and_install(self):
        self.download()
        return self.install()
