# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class BaseLanguageExport(models.TransientModel):
    _inherit = 'base.language.export'

    @api.model
    def default_get(self, fields):
        res = super(BaseLanguageExport, self).default_get(fields)
        if self.env['res.lang'].search([('code', '=', 'fr_FR')]):
            res.update({'lang': 'fr_FR', 'format': 'po'})
        return res


class BaseLanguageInstall(models.TransientModel):
    _inherit = 'base.language.install'

    @api.model
    def default_get(self, fields):
        res = super(BaseLanguageInstall, self).default_get(fields)
        if self.env['res.lang'].search([('code', '=', 'fr_FR')]):
            res.update({'lang': 'fr_FR', 'overwrite': True})
        return res


class BaseUpdateTranslations(models.TransientModel):
    _inherit = 'base.update.translations'

    @api.model
    def default_get(self, fields):
        res = super(BaseUpdateTranslations, self).default_get(fields)
        if self.env['res.lang'].search([('code', '=', 'fr_FR')]):
            res.update({'lang': 'fr_FR'})
        return res
