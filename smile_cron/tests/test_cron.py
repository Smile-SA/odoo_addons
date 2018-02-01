# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018 Smile (<http://www.smile.fr>). All Rights Reserved
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

from datetime import datetime, timedelta
import time

from openerp.tests.common import TransactionCase
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class CronTest(TransactionCase):
    """
        Basic testing of timesheet functionality added to ir.cron by smile_cron.
    """

    def setUp(self):
        super(CronTest, self).setUp()
        now = datetime.now()
        self.nextcall = now.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.numbercall = 4
        with self.registry.cursor() as new_cr:
            self.job_id = self.env['ir.cron'].with_env(self.env(cr=new_cr)).create({
                'name': 'test_cron',
                'nextcall': self.nextcall,
                'interval_type': 'minutes',
                'interval_number': 1,
                'numbercall': self.numbercall,
                'schedule_type': 'timesheet',
                'call_time_ids': [
                    (0, 0, {'call_time': now + timedelta(0, delay)})
                    for delay in (20, 40)
                ],
                'model': 'ir.cron',
                'function': 'search',
                'args': '([],)',
            }).id
    
    def tearDown(self):
        with self.registry.cursor() as new_cr:
            self.env['ir.cron']._model.unlink(new_cr, self.env.uid, [self.job_id], self.env.context)

    def _get_cron_field_value(self, field):
        with self.registry.cursor() as new_cr:
            Cron = self.env['ir.cron'].with_env(self.env(cr=new_cr))
            return Cron.browse(self.job_id)[field]

    def test_cron_timesheet(self):
        current_nextcall = self.nextcall
        while current_nextcall == self.nextcall:
            print "while 1"
            time.sleep(10)
            current_nextcall = self._get_cron_field_value('nextcall')
        current_numbercall = self._get_cron_field_value('numbercall')
        self.assertTrue(current_numbercall < self.numbercall,
                        "'numbercall' should be decremented")
        while current_numbercall:
            print "while 2"
            time.sleep(60)
            current_numbercall = self._get_cron_field_value('numbercall')
        self.assertFalse(self._get_cron_field_value('active'),
                         "When 'numbercall' reaches 0 job should switch to inactive")
