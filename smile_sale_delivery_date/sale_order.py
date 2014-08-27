# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>). All Rights Reserved
#                       author cyril.defaria@smile.fr
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
from openerp.osv import orm, fields
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _


class SaleOrder(orm.Model):
    _inherit = "sale.order"

    def _get_date_planned(self, cr, uid, order, line, start_date, context=None):
        return line.delivery_date


class SaleOrderLine(orm.Model):
    _inherit = "sale.order.line"

    _columns = {
        'delivery_date': fields.datetime("Date Expected")
    }

    def today_date(self, cr, uid, context=None):
        return datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    _defaults = {
        'delivery_date': today_date
    }
