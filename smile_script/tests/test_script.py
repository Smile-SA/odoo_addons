# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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


class ScriptTest(TransactionCase):

    def test_run(self):
        script = self.env['smile.script'].create({
            'name': 'Test',
            'type': 'python',
            'description': 'Test',
            'code': """
result = ustr(self.env['res.partner'].search([]))
result += ustr(self.pool['res.partner'].search(cr, uid, [], context=context))
            """,
        })
        script.with_context(do_not_use_new_cursor=True).run_test()
        self.assertTrue(script.intervention_ids[0].state == 'done')
