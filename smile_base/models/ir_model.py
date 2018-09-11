# -*- coding: utf-8 -*-
# (C) 2010 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from functools import partial

from odoo import api, models
from odoo.tools.translate import translate


class IrModelAccess(models.Model):
    _inherit = 'ir.model.access'

    @api.model_cr
    def group_names_with_access(self, model_name, access_mode):
        """ Translate group names in context or user lang.
        """
        res = super(IrModelAccess, self).group_names_with_access(
            model_name=model_name, access_mode=access_mode)
        lang = self._context.get('lang') or self.env.user.lang
        source_type = 'model'
        translated_res = []
        translate_group = partial(
            translate, self._cr, False, source_type, lang)
        for complete_name in res:
            if '/' in complete_name:
                category_name, group_name = complete_name.split('/')
                translated_name = "{}/{}".format(
                    translate_group(category_name),
                    translate_group(group_name))
            else:
                translated_name = '%s'.format(
                    translate_group(complete_name))
            translated_res.append(translated_name)
        return translated_res
