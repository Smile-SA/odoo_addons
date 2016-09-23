# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.tests.common import TransactionCase
from openerp.exceptions import ValidationError


class TestHolidays(TransactionCase):
    """
    """

    def setUp(self):
        super(TestHolidays, self).setUp()

        # User profile
        vals = {
            'name': 'Holidays Admin',
            'login': 'holidays_admin',
            'lang': 'en_US',
            'groups_id': [(4, self.ref('smile_holidays.group_manage_holidays'))],
        }
        self.holidays_admin = self.env['res.users'].create(vals)

        # Data
        self.area_a = self.env.ref('smile_holidays.res_holidays_area_a')
        self.area_b = self.env.ref('smile_holidays.res_holidays_area_b')
        self.department = self.env.ref('l10n_fr_department.res_country_department_aisne')
        for attribution in self.department.attribution_ids:
            self.department.write({'attribution_ids': [(2, attribution.id, 0)]})

    def test_invalid_holiday_dates(self):
        """
            I check that I can't create invalid holiday dates.
        """
        date_obj = self.env['res.holidays.date']
        vals = {
            'area_ids': [(4, self.area_a.id)],
            'start_date': '2015-10-25',
            'end_date': '2015-09-04', 'name': 'x',
        }
        with self.assertRaisesRegexp(ValidationError, "Start Date can't be after End Date!"):
            date_obj.sudo(self.holidays_admin).create(vals)

    def test_get_area_of_a_department_at_a_date(self):
        """
            I assign two areas to a department:
            - the effective date of the area A is 2015-01-01
            - the effective date of the area B is 2015-07-01
            I call the area effective for the departement at 2015-08-01
            I check that the returned area is B
            I call the area effective for the department at 2015-02-01
            I check that the returned area is A
        """
        attribution_obj = self.env['res.holidays.attribution']
        vals_list = [
            {'area_id': self.area_a.id, 'department_id': self.department.id,
             'effective_date': '2015/01/01'},
            {'area_id': self.area_b.id, 'department_id': self.department.id,
             'effective_date': '2015/07/01'},
        ]
        attribution_obj.bulk_create(vals_list)
        res = self.department.get_effective_area_at_a_date('2015-08-01')
        self.assertEquals(self.area_b, res, 'The expected area is B!')
        res = self.department.get_effective_area_at_a_date('2015-02-01')
        self.assertEquals(self.area_a, res, 'The expected area is A!')
