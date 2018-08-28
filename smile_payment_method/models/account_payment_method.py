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


class AccountPaymentMethod(models.Model):
    _name = 'account.payment.method'
    
    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True)
    journal_id = fields.Many2one('account.journal', string="Journal", domain=[('type', '=', ('bank', 'cash'))], required=False)
    active = fields.Boolean(string='Active')
