# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Smile (<http: //www.smile.fr>). All Rights Reserved
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
#    along with this program.  If not, see <http: //www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime

from osv import osv, fields
import tools
from tools.translate import _


class ResCountryHoliday(osv.osv):
    _name = 'res.country.holiday'
    _description = 'Public Holiday'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'date': fields.date('Date', required=True),
        'country_id': fields.many2one('res.country', 'Country', required=True, ondelete='restrict'),
    }

    def is_holiday(self, cr, uid, date_str, country_id, context=None):
        assert country_id, "country_id is mandatory"
        try:
            date = date_str and datetime.strptime(date_str, '%Y-%m-%d') or datetime.today()
        except ValueError, e:
            raise osv.except_osv(_('Format error !'), e)
        return bool(self.search(cr, uid, [('country_id', '=', country_id),
                                          ('date', '=', date.strftime('%Y-%m-%d')),
                                          ], limit=1, context=context))

    #Clear caches
    def create(self, cr, uid, vals, context=None):
        self.pool.get('res.company').clear_working_day_cache(cr)
        return super(ResCountryHoliday, self).create(cr, uid, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        self.pool.get('res.company').clear_working_day_cache(cr)
        return super(ResCountryHoliday, self).unlink(cr, uid, ids, context)

    def write(self, cr, uid, ids, vals, context=None):
        self.pool.get('res.company').clear_working_day_cache(cr)
        return super(ResCountryHoliday, self).write(cr, uid, ids, vals, context)

ResCountryHoliday()


class ResCountry(osv.osv):
    _inherit = 'res.country'

    _columns = {
        'holiday_ids': fields.one2many('res.country.holiday', 'country_id', 'Holidays'),
    }

    #Clear caches
    def create(self, cr, uid, vals, context=None):
        self.pool.get('res.company').clear_working_day_cache(cr)
        return super(ResCountry, self).create(cr, uid, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        self.pool.get('res.company').clear_working_day_cache(cr)
        return super(ResCountry, self).unlink(cr, uid, ids, context)

    def write(self, cr, uid, ids, vals, context=None):
        self.pool.get('res.company').clear_working_day_cache(cr)
        return super(ResCountry, self).write(cr, uid, ids, vals, context)

ResCountry()


class ResCompanyDayOff(osv.osv):
    _name = 'res.company.dayoff'
    _description = 'Days Off'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'date': fields.date('Date', required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True, ondelete='restrict'),
    }

    def is_day_off(self, cr, uid, date_str, company_id, context=None):
        assert company_id, "company_id is mandatory"
        try:
            date = date_str and datetime.strptime(date_str, '%Y-%m-%d') or datetime.today()
        except ValueError, e:
            raise osv.except_osv(_('Format error !'), e)

        company = self.pool.get('res.company').read(cr, uid, company_id, ['parent_id', 'inherit_dayoff'], context, load='_classic_write')
        if company['inherit_dayoff']:
            return self.is_day_off(cr, uid, date, company['parent_id'], context)
        return bool(self.search(cr, uid, [('company_id', '=', company_id),
                                          ('date', '=', date.strftime('%Y-%m-%d'))], limit=1, context=context))

    #Clear caches
    def create(self, cr, uid, vals, context=None):
        self.pool.get('res.company').clear_working_day_cache(cr)
        return super(ResCompanyDayOff, self).create(cr, uid, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        self.pool.get('res.company').clear_working_day_cache(cr)
        return super(ResCompanyDayOff, self).unlink(cr, uid, ids, context)

    def write(self, cr, uid, ids, vals, context=None):
        self.pool.get('res.company').clear_working_day_cache(cr)
        return super(ResCompanyDayOff, self).write(cr, uid, ids, vals, context)

ResCompanyDayOff()


class ResCompany(osv.osv):
    _inherit = 'res.company'

    _columns = {
        'mon': fields.boolean('Monday'),
        'tue': fields.boolean('Tuesday'),
        'wed': fields.boolean('Wednesday'),
        'thu': fields.boolean('Thursday'),
        'fri': fields.boolean('Friday'),
        'sat': fields.boolean('Saturday'),
        'sun': fields.boolean('Sunday'),
        'dayoff_ids': fields.one2many('res.company.dayoff', 'company_id', 'Days off'),
        'country_id': fields.related('partner_id', 'country', type='many2one', relation='res.country', string='Country', store=True, readonly=True),
        'inherit_dayoff': fields.boolean('Inherit days off and weekdays from parent company ?'),
    }

    _defaults = {
        'sat': True,
        'sun': True,
    }

    def _check_inherit(self, cr, uid, ids, context=None):
        for company in self.read(cr, uid, ids, ['inherit_dayoff', 'parent_id'], context):
            if company['inherit_dayoff'] and not company['parent_id']:
                return False
        return True

    _constraints = [(_check_inherit, _('You cannot inherit off days if you have no parent company!'), ['inherit_dayoff', 'parent_id'])]

    def is_working_day(self, cr, uid, company_id, date_str, context=None):
        """Returns True if the day is off, False otherwise.
        A working day is:
            A weekday that is not off,
            A date that is not closed for the company
            A date that is not off for the country of the company"""
        company = self.read(cr, uid, company_id, ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun', 'country_id', 'inherit_dayoff', 'parent_id'], context, load='_classic_write')
        if company['inherit_dayoff']:
            return self.is_working_day(cr, uid, company['parent_id'], date_str, context)

        day_mapping = {0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu', 4: 'fri', 5: 'sat', 6: 'sun'}
        return bool(not company[day_mapping[datetime.strptime(date_str, '%Y-%m-%d').weekday()]]
                    and not self.pool.get('res.company.dayoff').is_day_off(cr, uid, date_str, company['id'])
                    and not self.pool.get('res.country.holiday').is_holiday(cr, uid, date_str, company['country_id']))

    def get_num_working_days(self, cr, uid, company_id, start_date, end_date, context=None):
        """Returns the number of working days between two dates for the given company.
        A working day is:
            A weekday that is not off,
            A date that is not closed for the company
            A date that is not off for the country of the company"""
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        if start_date > end_date:
            start_date, end_date = end_date, start_date

        count = 0
        curr_date = start_date
        while(curr_date <= end_date):
            if self.is_working_day(cr, uid, company_id, curr_date.strftime(date_format), context):
                count = count + 1
            curr_date = curr_date + datetime.timedelta(days=1)
        return count

    @tools.cache(skiparg=3)
    def cached_is_working_day(self, cr, uid, company_id, date_str):
        return self.is_working_day(cr, uid, company_id, date_str)

    def clear_working_day_cache(self, cr):
        self.cached_is_working_day.clear_cache(cr.dbname)

    #Clear caches
    def create(self, cr, uid, vals, context=None):
        self.pool.get('res.company').clear_working_day_cache(cr)
        return super(ResCompany, self).create(cr, uid, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        self.pool.get('res.company').clear_working_day_cache(cr)
        return super(ResCompany, self).unlink(cr, uid, ids, context)

    def write(self, cr, uid, ids, vals, context=None):
        self.pool.get('res.company').clear_working_day_cache(cr)
        return super(ResCompany, self).write(cr, uid, ids, vals, context)

ResCompany()


class ResPartner(osv.osv):
    _inherit = 'res.partner'

    def write(self, cr, uid, ids, vals, context=None):
        if 'country_id' in vals:
            self.pool.get('res.company').clear_working_day_cache(cr)
        return super(ResPartner, self).write(cr, uid, ids, vals, context)

ResPartner()
