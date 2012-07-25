# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
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

from osv import fields, osv
from tools.translate import _


class account_invoicing_plan(osv.osv):
    _name = 'account.invoicing_plan'

    _columns = {
        'name': fields.char('Name', size=64, required=True, select=True),
        'trigger': fields.selection([
            ('manual', 'on Sales Order'),
            ('picking', 'on Delivery'),
        ], 'Trigger', required=True),
        'periodicity': fields.integer('Periodicity', required=True),
        'commitment': fields.integer('Commitment', required=True, help='Expressed in months'),
        'uop': fields.selection([
            ('months', 'Months'),
        ], 'Unit Of Periods', required=True),
        'term': fields.selection([
            ('unlimited', 'Unlimited'),
            ('fixed', 'Fixed'),
        ], 'Term', required=True),
        'mode': fields.selection([
            ('pre', 'Pre-invoicing'),
            ('post', 'Post-invoicing'),
        ], 'Invoicing mode', required=True),


    }

    _defaults = {
        'trigger': lambda * a: 'manual',
        'periodicity': lambda * a: 1,
        'commitment': lambda * a: 12,
        'uop': lambda * a: 'months',
        'term': lambda * a: 'unlimited',
        'mode': lambda * a: 'post',

    }
account_invoicing_plan()


class account_invoicing_plan_sub_line(osv.osv):
    _name = 'account.invoicing_plan.sub.line'

    _columns = {
        'name': fields.char('Name', size=64),
        'value': fields.selection([
            ('fixed', 'Fixed Amount'),
            ('percent', 'Percent'),
            ('balance', 'Balance'),
        ], 'Valuation', required=True, help="""Select here the kind of valuation related to this payment term line. Note that you should have your last line with the type 'Balance' to ensure that the whole amount will be threated."""),
        'value_amount': fields.float('Value Amount', help="For Value percent enter % ratio between 0-1."),
        'partner': fields.selection([
            ('object.partner_id.id', 'Partner'),
            ('object.partner_id.parent_id.id', 'Parent'),
        ], 'Partner', required=True),
       # 'invoicing_plan_line_id': fields.many2one('account.invoicing_plan.line', 'Invoicing plan modality', required=True),
    }

    _defaults = {
        'name': 'sous modalite',
        #'partner': lambda * a: 'object.partner_id.id',
    }

account_invoicing_plan_sub_line()


class account_invoicing_plan_line(osv.osv):
    _name = 'account.invoicing_plan.line'

    _columns = {
        'name': fields.char('Name', size=64, required=True, select=True),
        'invoicing_plan_id': fields.many2one('account.invoicing_plan', 'Invoicing Plan', required=True),
        'sequence': fields.integer('Sequence', required=True),
        'invoicing_plan_sub_line_ids': fields.one2many('account.invoicing_plan.sub.line', 'invoicing_plan_line_id', 'Sub modalities', required=False),
#        'value': fields.selection([
#            ('fixed', 'Fixed Amount'),
#            ('percent', 'Percent'),
#            ('balance', 'Balance'),
#        ], 'Valuation', required=True, help="""Select here the kind of valuation related to this payment term line. Note that you should have your last line with the type 'Balance' to ensure that the whole amount will be threated."""),
#        'value_amount': fields.float('Value Amount', help="For Value percent enter % ratio between 0-1."),
        'application_periods': fields.char('Application Periods', size=64, required=True),
#        'partner': fields.selection([
#            ('object.partner_id.id', 'Partner'),
#            ('object.partner_id.parent_id.id', 'Parent'),
#        ], 'Partner', required=True),
    }

    _defaults = {
        'application_periods': lambda * a: '0',
#        'partner': lambda * a: 'object.partner_id.id',
    }

    def _check_application_periods(self, cr, uid, ids):
        for line in self.browse(cr, uid, ids):
            periods = line.application_periods.replace(' ', '').split(', ')
            for period in periods:
                if not isinstance(eval(period), int):
                    return False
        return True

    _contraints = [
        (_check_application_periods, _("The field 'Application Periods' is a list of integers"), ['application_periods']),
    ]
account_invoicing_plan_line()


class account_invoicing_plan_sub_line(osv.osv):
    _inherit = 'account.invoicing_plan.sub.line'

    _columns = {

        'invoicing_plan_line_id': fields.many2one('account.invoicing_plan.line', 'Invoicing plan modality', required=False),
    }

    _defaults = {
        'name': 'sous modalite',
        'partner': lambda * a: 'object.partner_id.id',
    }

account_invoicing_plan_sub_line()


class account_invoicing_plan(osv.osv):
    _inherit = 'account.invoicing_plan'

    _columns = {
        'line_ids': fields.one2many('account.invoicing_plan.line', 'invoicing_plan_id', 'Modalities'),
    }
account_invoicing_plan()



