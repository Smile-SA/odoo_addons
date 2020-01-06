# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from functools import partial

from odoo import api, models


class IrModelAccess(models.Model):
    _inherit = 'ir.model.access'

    @api.model
    def group_names_with_access(self, model_name, access_mode):
        """ Translate group names in context or user lang.
        """
        res = super(IrModelAccess, self).group_names_with_access(
            model_name=model_name, access_mode=access_mode)
        lang = self._context.get('lang') or self.env.user.lang
        translated_res = []
        translate_group = partial(
            self.env['ir.translation']._get_source, None, 'model', lang)
        for complete_name in res:
            if '/' in complete_name:
                category_name, group_name = complete_name.split('/')
                translated_name = "{}/{}".format(
                    translate_group(category_name) or category_name,
                    translate_group(group_name) or group_name)
            else:
                translated_name = '{}'.format(
                    translate_group(complete_name) or complete_name)
            translated_res.append(translated_name)
        return translated_res
