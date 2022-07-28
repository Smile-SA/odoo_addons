# -*- coding: utf-8 -*-
# (C) 2022 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, SUPERUSER_ID
from odoo.tools import config


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['admin.passwd'].create_or_set_passwd(config.get('admin_passwd'))
