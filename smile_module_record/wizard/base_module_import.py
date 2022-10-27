# -*- coding: utf-8 -*-
# (C) 2011 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from io import BytesIO
import logging
import os.path
import re
import zipfile

from odoo import api, fields, models, modules, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__package__)


class BaseModuleImport(models.TransientModel):
    _name = 'base.module.import'
    _description = "Base Module Import"

    module_name = fields.Char(required=True, help="Technical name")
    file = fields.Binary(required=True)

    @api.constrains('module_name')
    def _check_module_name(self):
        self.ensure_one()
        invalid_characters = re.findall(r'[^A-Za-z0-9_\-]', self.module_name)
        if invalid_characters:
            raise UserError(
                _("Invalid characters in module name: '%s'") %
                "', '".join(invalid_characters))
        if self.env['ir.module.module'].search_count(
                [('name', '=', self.module_name)]):
            raise UserError(
                _("The module '%s' already exists") % self.module_name)

    @api.constrains('file')
    def _check_zipfile(self):
        self.ensure_one()
        filecontent = self._get_file_content()
        module_file = BytesIO()
        module_file.write(filecontent)
        if not zipfile.is_zipfile(module_file):
            raise UserError(_('File is not a zip file!'))

    def _get_file_content(self):
        self.ensure_one()
        return base64.decodebytes(self.file)

    def _get_module_path(self):
        self.ensure_one()
        module_path = modules.get_module_path(
            '', downloaded=True, display_warning=False)
        return os.path.join(module_path, self.module_name)

    def download(self):
        filecontent = self._get_file_content()
        module_path = self._get_module_path()
        zipfile.ZipFile(BytesIO(filecontent)).extractall(module_path)
        return self.env['ir.module.module'].sudo().update_list()

    def install(self):
        self.ensure_one()
        modules = self.env['ir.module.module'].sudo().search(
            [('name', '=', self.module_name)])
        return modules.button_immediate_install()

    def download_and_install(self):
        self.download()
        return self.install()
