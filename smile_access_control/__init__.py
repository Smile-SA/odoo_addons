# -*- coding: utf-8 -*-
# (C) 2022 Smile (<https://www.smile.eu>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from . import models

from odoo import api, SUPERUSER_ID


def uninstall_hook(cr, registry):
    """ Reset domain of native user act window.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.ref('base.action_res_users').domain = []
