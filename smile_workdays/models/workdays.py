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

from datetime import timedelta

from openerp import api, fields, models, tools, _
from openerp.exceptions import Warning

from ..tools import ClearWorkingDayCache, clean_date


@ClearWorkingDayCache
class ResCountryHoliday(models.Model):
    _name = 'res.country.holiday'
    _description = 'Public Holiday'

    name = fields.Char(required=True)
    date = fields.Date(required=True)
    country_id = fields.Many2one('res.country', 'Country', required=True, ondelete='restrict')


@ClearWorkingDayCache
class ResCountry(models.Model):
    _inherit = 'res.country'

    holiday_ids = fields.One2many('res.country.holiday', 'country_id', 'Holidays')

    @api.multi
    def is_holiday(self, date_to_check):
        self.ensure_one()
        date_to_check = clean_date(date_to_check)
        return bool(self.holiday_ids.filtered(lambda holiday: holiday.date == date_to_check.strftime('%Y-%m-%d')))


@ClearWorkingDayCache
class ResCompanyDayOff(models.Model):
    _name = 'res.company.dayoff'
    _description = 'Days Off'

    name = fields.Char(required=True)
    date = fields.Date(required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, ondelete='restrict')


@ClearWorkingDayCache
class ResCompany(models.Model):
    _inherit = 'res.company'

    mon = fields.Boolean('Monday')
    tue = fields.Boolean('Tuesday')
    wed = fields.Boolean('Wednesday')
    thu = fields.Boolean('Thursday')
    fri = fields.Boolean('Friday')
    sat = fields.Boolean('Saturday', default=True)
    sun = fields.Boolean('Sunday', default=True)
    dayoff_ids = fields.One2many('res.company.dayoff', 'company_id', 'Days off')
    country_id = fields.Many2one('res.country', 'Country', related='partner_id.country_id', store=True, readonly=True)
    inherit_dayoff = fields.Boolean('Inherit days off and weekdays from parent company ?')

    @api.one
    @api.constrains('inherit_dayoff', 'parent_id')
    def _check_inherit(self):
        if self.inherit_dayoff and not self.parent_id:
            raise Warning(_('You cannot inherit off days if you have no parent company!'))

    @api.multi
    def is_day_off(self, date_to_check):
        self.ensure_one()
        date_to_check = clean_date(date_to_check)
        if self.inherit_dayoff:
            return self.parent_id.is_day_off(date_to_check)
        return bool(self.dayoff_ids.filtered(lambda dayoff: dayoff.date == date_to_check.strftime('%Y-%m-%d')))

    @api.multi
    def _is_working_day(self, date_to_check):
        """Returns True if the day is a working day, False otherwise.
        A working day is:
            A weekday that is not off,
            A date that is not closed for the company
            A date that is not off for the country of the company"""
        self.ensure_one()
        date_to_check = clean_date(date_to_check)
        if self.inherit_dayoff:
            return self.parent_id.is_working_day(date_to_check)
        day_mapping = {0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu', 4: 'fri', 5: 'sat', 6: 'sun'}
        if getattr(self, day_mapping[date_to_check.weekday()]):
            return False
        if self.is_day_off(date_to_check):
            return False
        if self.country_id and self.country_id.is_holiday(date_to_check):
            return False
        return True

    @tools.cache(skiparg=3)
    def _cached_is_working_day(self, cr, uid, company_id, date_to_check):
        return self.browse(cr, uid, company_id)._is_working_day(date_to_check)

    def clear_is_working_day_cache(self):
        self._cached_is_working_day.clear_cache(self)

    @api.multi
    def is_working_day(self, date_to_check):
        return self._model._cached_is_working_day(self._cr, self._uid, self.env.user.company_id.id, date_to_check)

    @api.multi
    def get_working_days_delta(self, start_date, end_date):
        """Returns the number of working days between two dates for the given company.
        A working day is:
            A weekday that is not off,
            A date that is not closed for the company
            A date that is not off for the country of the company"""
        self.ensure_one()
        start_date = clean_date(start_date)
        end_date = clean_date(end_date)
        if start_date > end_date:
            start_date, end_date = end_date, start_date
        count = 0
        curr_date = start_date
        while curr_date <= end_date:
            if self.is_working_day(curr_date.strftime('%Y-%m-%d')):
                count += 1
            curr_date += timedelta(days=1)
        return count
