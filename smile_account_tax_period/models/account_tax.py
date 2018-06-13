# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    date_start = fields.Date('Start Date')
    date_stop = fields.Date('End Date')
