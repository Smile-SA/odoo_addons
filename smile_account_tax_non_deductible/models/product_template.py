# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    admission_rate_ids = fields.One2many(
        'account.tax.rate', 'product_tmpl_id', 'Admission rates',
        domain=[('rate_type', '=', 'admission')],
        context={'default_rate_type': 'admission'})
    subjugation_rate_ids = fields.One2many(
        'account.tax.rate', 'product_tmpl_id', 'Subjugation rates',
        domain=[('rate_type', '=', 'subjugation')],
        context={'default_rate_type': 'subjugation'})
