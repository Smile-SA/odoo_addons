# (C) 2025 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.fields import Field
from odoo.addons.smile_decimal_precision.models import DecimalPrecision as dp


native_get_description = Field.get_description


def new_get_description(self, env, attributes=None):
    desc = native_get_description(self, env, attributes)
    if hasattr(self, '_related__digits') and isinstance(self._related__digits,
                                                        str):
        application = self._related__digits
        desc['digits'] = dp.get_display_precision(env,
                                                  application)
    return desc


Field.get_description = new_get_description
