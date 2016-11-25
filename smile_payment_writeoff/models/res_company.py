# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields, models
import odoo.addons.decimal_precision as dp


class ResCompany(models.Model):
    _inherit = 'res.company'

    invoice_loss_amount = fields.Float(string='Max Loss Amount', digits=dp.get_precision('Account'))
    invoice_profit_amount = fields.Float(string='Max Profit Amount', digits=dp.get_precision('Account'))
    invoice_loss_account_id = fields.Many2one('account.account', 'Loss Account', ondelete='restrict')
    invoice_profit_account_id = fields.Many2one('account.account', 'Profit Account', ondelete='restrict')
