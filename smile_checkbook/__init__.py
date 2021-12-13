# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from . import models
from . import wizard

from odoo import api, SUPERUSER_ID


def account_checkbook_wizard(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    account_check = env['account.check'].search_count([
        ('number', '>=', '12200341'),
        ('number', '<=', '12200360'),
    ])

    if not account_check:
        line = env['account.checkbook.wizard'].create({
            'partner_id': env.ref('base.res_partner_address_4', raise_if_not_found=False).id,
            'company_id': env.ref('base.main_company', raise_if_not_found=False).id,
            'quantity': 20,
            'from_number': 12200341,
            'to_number': 12200360,
        })
        line.generate_checks()
