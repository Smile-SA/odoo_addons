# -*- coding: utf-8 -*-

from odoo import api, SUPERUSER_ID

import models


def _update_models(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {'todo': []})
    for model in env.values():
        model._auto_init()
