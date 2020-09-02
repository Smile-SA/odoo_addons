# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, SUPERUSER_ID

from . import models


def _update_models(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {'todo': []})
    for model in env.values():
        model._auto_init()
