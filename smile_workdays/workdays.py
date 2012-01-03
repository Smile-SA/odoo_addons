# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011 EFFIA (<http://www.effia.fr>). All Rights Reserved
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

import datetime, time

from osv import osv, fields
from tools.translate import _

day_mapping = {0:'mon', 1:'tue', 2:'wed', 3:'thu', 4:'fri', 5:'sat', 6:'sun'}

date_format = '%Y-%m-%d'

def date_from_openerp_str(date_str):
    return datetime.datetime.fromtimestamp(time.mktime(time.strptime(date_str, date_format))).date()

class ResCountryHoliday(osv.osv):
    _name = 'res.country.holiday'
    _description = 'Public Holiday'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'day': fields.integer('Day', required=True),
        'month': fields.integer('Month', required=True),
        'country_id': fields.many2one('res.country', 'Country', required=True),
    }

    def _check_valid_date(self, cr, uid, ids, context=None):
        for country in self.read(cr, uid, ids, ['day', 'month'], context):
            if not country['day'] or not country['month']:
                return False
            if country['month'] == 2 and country['day'] <= 29:
                continue
            try:
                datetime.date(2000, country['month'], country['day'])
            except Exception:
                return False
        return True

    _constraints = [(_check_valid_date, 'You cannot define a date which will never exist in any calendar !', ['day', 'month'])]

    def is_holiday(self, cr, uid, date='', country_id=False, context=None):
        date = date or time.strftime(date_format)
        day = int(date[8:])
        month = int(date[5:7])
        if not isinstance(date, (str, unicode)):
            raise osv.except_osv(_('Error'), _('Date must be a string!'))
        domain = [('month', '=', month), ('day', '=', day)]
        if country_id:
            domain.append(('country_id', '=', country_id))
        return bool(self.search(cr, uid, domain, limit=1, context=context))
ResCountryHoliday()

class ResCountry(osv.osv):
    _inherit = 'res.country'

    _columns = {
        'holiday_ids': fields.one2many('res.country.holiday', 'country_id', 'Holidays'),
    }
ResCountry()

class ResCompanyDayOff(osv.osv):
    _name = 'res.company.dayoff'
    _description = 'Days Off'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'date': fields.date('Date', required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }

    def is_day_off(self, cr, uid, date=False, company_id=False, context=None):
        date = date or time.strftime(date_format)
        if not isinstance(date, (str, unicode)):
            raise osv.except_osv(_('Error'), _('Date must be a string!'))
        domain = [('date', '=', date)]
        if company_id:
            company = self.pool.get('res.company').read(cr, uid, [company_id], ['parent_id', 'inherit_dayoff'], context, load='_classic_write')[0]
            if company['inherit_dayoff']:
                return self.is_day_off(cr, uid, date, company['parent_id'], context)
            else:
                domain.append(('company_id', '=', company_id))
        return bool(self.search(cr, uid, domain, limit=1, context=context))
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

    def is_working_day(self, cr, uid, company_id, date, context=None):
        """Returns True if the day is off, False otherwise.
        A working day is :
            A weekday that is not off,
            A date that is not closed for the company
            A date that is not off for the country of the company"""
        if isinstance(company_id, (int, long)):
            company_id = [company_id]
        company = self.read(cr, uid, company_id, ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun', 'country_id', 'inherit_dayoff', 'parent_id'], context, load='_classic_write')[0]
        if company['inherit_dayoff']:
            return self.is_working_day(cr, uid, company['parent_id'], date, context)
        return bool(not company[day_mapping[date_from_openerp_str(date).weekday()]] \
            and not self.pool.get('res.company.dayoff').is_day_off(cr, uid, date, company['id']) \
            and not self.pool.get('res.country.holiday').is_holiday(cr, uid, date, company['country_id']))


    def get_num_working_days(self, cr, uid, company_id, start_date, end_date, context=None):
        """Returns the number of working days between two dates for the given company.
        A working day is :
            A weekday that is not off,
            A date that is not closed for the company
            A date that is not off for the country of the company"""
        if isinstance(company_id, (int, long)):
            company_id = [company_id]
        start_date = date_from_openerp_str(start_date)
        end_date = date_from_openerp_str(end_date)

        if start_date > end_date:
            tmp = start_date
            start_date = end_date
            end_date = tmp

        count = 0
        curr_date = start_date
        while(curr_date <= end_date):
            if self.is_working_day(cr, uid, company_id, curr_date.strftime(date_format), context):
                count = count + 1
            curr_date = curr_date + datetime.timedelta(days=1)

        return count
ResCompany()
