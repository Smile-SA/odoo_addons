# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp import api, models


class BaseLanguageExport(models.TransientModel):
    _inherit = 'base.language.export'

    @api.model
    def default_get(self, fields):
        res = super(BaseLanguageExport, self).default_get(fields)
        res.update({'lang': 'fr_FR', 'format': 'po'})
        return res


class BaseLanguageInstall(models.TransientModel):
    _inherit = 'base.language.install'

    @api.model
    def default_get(self, fields):
        res = super(BaseLanguageInstall, self).default_get(fields)
        res.update({'lang': 'fr_FR', 'overwrite': True})
        return res


class BaseUpdateTranslations(models.TransientModel):
    _inherit = 'base.update.translations'

    @api.model
    def default_get(self, fields):
        res = super(BaseUpdateTranslations, self).default_get(fields)
        res.update({'lang': 'fr_FR'})
        return res
