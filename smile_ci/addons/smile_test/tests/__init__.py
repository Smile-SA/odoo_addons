# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from distutils.version import LooseVersion

try:
    from odoo import release
except ImportError:
    pass
else:
    if LooseVersion(release.major_version) >= LooseVersion('12.0'):
        from . import test_act_window
        from . import test_fields_view_get
        from . import test_general_read
        from . import test_ir_rule
