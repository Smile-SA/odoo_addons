# -*- encoding: utf-8 -*-
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountCheckbookWizard(models.TransientModel):
    _name = 'account.checkbook.wizard'
    _description = 'Account Checkbook Wizard'

    partner_id = fields.Many2one('res.partner', 'Partner', required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True)
    from_number = fields.Integer('From Number')
    to_number = fields.Integer('To Number')
    quantity = fields.Integer('Quantity')

    @api.onchange('from_number', 'quantity', 'to_number')
    def onchange_range_of_numbers(self):
        if self.quantity:
            self.to_number = self.from_number + self.quantity
        elif self.to_number:
            self.quantity = self.to_number - self.from_number

    @api.onchange('partner_id')
    def onchange_partner(self):
        if self.partner_id:
            self.company_id = self.partner_id.company_id

    @api.multi
    def generate_checks(self):
        self.ensure_one()
        AccountCheck = self.env['account.check']
        if not (self.from_number and self.to_number):
            raise UserError(
                _("Please define a range of numbers before generating checks"))
        if self.from_number > self.to_number:
            raise UserError(
                _("Minimal number is greather than maximum number. "
                    "Please check range of numbers."))
        if not self.from_number + self.quantity == self.to_number:
            raise UserError(
                _("Quantity seems inconsistent with range of numbers"))
        common_vals = {
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'state': 'available',
        }
        vals_list = []
        for number in range(self.from_number, self.to_number):
            vals_list.append(dict(common_vals, number=number))
        AccountCheck.bulk_create(vals_list)
        # Refresh check tree view
        action = self.env.ref('smile_checkbook.action_account_check')
        return {
            'name': _(action.name),
            'type': action.type,
            'res_model': action.res_model,
            'view_mode': action.view_mode,
            'target': 'current',
        }
