# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from . import models

from odoo.api import Environment, SUPERUSER_ID


def post_init_hook(cr, registry):
    # Add act_window id in context
    env = Environment(cr, SUPERUSER_ID, {})
    env['ir.actions.act_window'].with_context(active_test=False).search([])._update_context()

