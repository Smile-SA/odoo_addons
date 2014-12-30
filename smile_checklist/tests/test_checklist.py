# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp.tests.common import TransactionCase


class TestChecklist(TransactionCase):

    def test_create_cron(self):
        """
            1. I get a cron checklist controlling that the Object is filled.
        """
        checklist = self.env.ref('smile_checklist.cron_checklist')
        cron = self.env['ir.cron'].create({'name': 'Demo cron'})
        self.assertFalse(cron.active, 'Cron is active whereas the Object is not filled.')
        cron.model = 'some.model'
        self.assertTrue(cron.active, 'Cron is inactive whereas the Object is filled.')
