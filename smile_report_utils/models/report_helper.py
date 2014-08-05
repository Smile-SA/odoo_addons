# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp.addons.report_webkit.report_helper import WebKitHelper


native_init = WebKitHelper.__init__


def new_init(self, cr, uid, report_id, context):
    native_init(self, cr, uid, report_id, context)
    self.context = context

WebKitHelper.__init__ = new_init


def get_report_title(self):
    return self.pool.get('ir.actions.report.xml').read(self.cursor, self.uid, self.report_id, ['name'], self.context)['name']

WebKitHelper.get_report_title = get_report_title
