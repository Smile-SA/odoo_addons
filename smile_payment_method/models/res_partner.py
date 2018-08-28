# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp import models, fields, api, exceptions
from openerp.tools.translate import _


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    @api.model
    def _get_default_payment_method(self):
        modes = self.env['account.payment.method'].search([], limit=1)
        return modes or self.env['account.payment.method']
    
    payment_method_suppliers_id = fields.Many2one('account.payment.method',
                                                        string='Payment Method Suppliers',
                                                        help="This payment method will be used instead of the default one ",
                                                        default=_get_default_payment_method)
    payment_method_customer_id = fields.Many2one('account.payment.method',
                                                        string='Payment Method Customer',
                                                        help="This payment method will be used instead of the default one ",
                                                        default=_get_default_payment_method)
    
