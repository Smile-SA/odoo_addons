# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountExportTemplate(models.Model):
    _inherit = 'account.export.template'

    provider = fields.Selection(selection_add=[
        ('sage', 'Sage'),
    ])
