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

from openerp import api, fields, models, _
from openerp.exceptions import UserError


class ResHolidaysArea(models.Model):
    _name = 'res.holidays.area'
    _description = 'Holidays Area'

    name = fields.Char(required=True)
    holiday_date_ids = fields.Many2many('res.holidays.date', 'res_holidays_area_res_holiday_date_rel',
                                        'area_id', 'date_id', 'Holidays Dates')
    attribution_ids = fields.One2many('res.holidays.attribution', 'area_id', "Attributions")


class ResHolidaysDate(models.Model):
    _name = 'res.holidays.date'
    _description = 'Holidays Date'

    name = fields.Char(required=True)
    area_ids = fields.Many2many('res.holidays.area', 'res_holidays_area_res_holiday_date_rel',
                                'date_id', 'area_id', 'Holidays Areas')
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)

    @api.one
    @api.constrains('start_date', 'end_date', 'area_ids')
    def _check_dates(self):
        if self.start_date > self.end_date:
            raise UserError(_("Start Date can't be after End Date!"))
        for area in self.area_ids:
            holidays_dates = self.search(['&', '&', ('area_ids', 'in', area.id), ('id', '!=', self.id), '|',
                                          '&', ('start_date', '>=', self.start_date), ('start_date', '<=', self.end_date), '|',
                                          '&', ('end_date', '<=', self.end_date), ('end_date', '>=', self.start_date),
                                          '&', ('start_date', '<=', self.start_date), ('end_date', '>=', self.end_date)])
            if holidays_dates:
                holiday = holidays_dates[0]
                raise UserError(_("The holiday period {} is already declared for zone {} between {} and {}")
                                .format(holiday.name, area.name, holiday.start_date, holiday.end_date,))

    @api.multi
    def name_get(self):
        return [(date.id, _("(%s) From %s to %s") % (date.name, date.start_date, date.end_date))
                for date in self]


class ResHolidaysAttribution(models.Model):
    _name = 'res.holidays.attribution'
    _description = 'Holidays Attribution'
    _order = 'effective_date, department_id'

    area_id = fields.Many2one('res.holidays.area', 'Holidays Area', required=True, ondelete='restrict')
    department_id = fields.Many2one('res.country.department', 'Department', required=True,
                                    ondelete='restrict')
    effective_date = fields.Date(required=True,
                                 help="The area starts to be active at this date")


class ResCountryDepartment(models.Model):
    _inherit = 'res.country.department'

    attribution_ids = fields.One2many('res.holidays.attribution', 'department_id', 'Effective areas')

    @api.one
    @api.returns('res.holidays.area', lambda area: area.id)
    def get_effective_area_at_a_date(self, date):
        """
        Returns the effective area for this department at a date.

        @param date: fields.Str
        @return: res.holidays.area
        """
        res = self.env['res.holidays.area'].browse()
        attribution_ids = self.attribution_ids.filtered(lambda attribution:
                                                        attribution.effective_date <= date)
        if attribution_ids:
            res = attribution_ids.sorted(lambda self: self.effective_date, reverse=True)[0].area_id
        return res
