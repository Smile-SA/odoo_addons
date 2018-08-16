# -*- coding: utf-8 -*-
# (C) 2010 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, tools


class PublisherWarrantyContract(models.AbstractModel):
    _inherit = "publisher_warranty.contract"

    @api.multi
    def update_notification(self, cron_mode=True):
        if not tools.config.get(
                'enable_publisher_warranty_contract_notification'):
            return True
        return super(PublisherWarrantyContract, self). \
            update_notification(cron_mode)
