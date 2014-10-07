# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>). All Rights Reserved
#                       author cydef@smile.fr
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

from openerp.osv import (orm, fields)
import openerp.addons.connector.backend as backend
import openerp.addons.magentoerpconnect.backend as magento_backend

ecommerce = backend.Backend(parent=magento_backend.magento1700, version='ecommerce')

class MagentoBackend(orm.Model):
    _inherit = 'connector.backend'

    def select_versions(self, cr, uid, context=None):
        """ Available versions in the backend.

        Can be inherited to add custom versions.  Using this method
        to add a version from an ``_inherit`` does not constrain
        to redefine the ``version`` field in the ``_inherit`` model.
        """
        return [('ecommerce', 'ECommerce')]

