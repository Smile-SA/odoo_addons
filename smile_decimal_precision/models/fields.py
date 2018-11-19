# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.fields import Field

from odoo.addons.smile_decimal_precision.models import DecimalPrecision as dp


native_get_description = Field.get_description


def new_get_description(self, env):
    desc = native_get_description(self, env)
    if getattr(self, '_digits', None) and callable(self._digits) and \
            self._digits.__closure__:
        application = self._digits.__closure__[0].cell_contents
        desc['digits'] = dp.get_display_precision(env, application)
    return desc


Field.get_description = new_get_description
