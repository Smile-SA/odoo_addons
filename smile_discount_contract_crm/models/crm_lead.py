# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    nb_of_discount_contracts = fields.Integer(compute='_get_discount_contracts')

    @api.one
    def _get_discount_contracts(self):
        self.nb_of_discount_contracts = self.env['discount.contract']. \
            search_count([('opportunity_id', '=', self.id)])
