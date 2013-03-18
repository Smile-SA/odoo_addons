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

import base64
from datetime import datetime
import dateutil
from dateutil.relativedelta import relativedelta
import time
import urllib2

import openerp.addons.decimal_precision as dp
from openerp.modules.registry import Registry
from openerp.osv import orm, fields
from openerp.tools import image_get_resized_images, image_resize_image_big
from openerp.tools.func import wraps
from openerp.tools.translate import _

FREQUENCIES = [('monthly', 'Monthly or more'), ('daily', 'From daily to bi-monthly')]
MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']


class PublicationPublication(orm.Model):
    _name = 'publication.publication'
    _description = "Publication"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    def _has_image(self, cr, uid, ids, name, args, context=None):
        res = {}
        for publication in self.browse(cr, uid, ids, context):
            res[publication.id] = bool(publication.image or publication.image_url)
        return res

    def _get_image(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for publication in self.browse(cr, uid, ids, context):
            if publication.image_url:
                try:
                    image = urllib2.urlopen(publication.image_url).read()
                    image = base64.b64encode(image)
                    res[publication.id] = image_get_resized_images(image)['image_small']
                except:
                    pass
            elif publication.image:
                res[publication.id] = image_get_resized_images(publication.image)['image_small']
        return res

    def _set_image(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'image': image_resize_image_big(value)}, context=context)

    def _get_number_count(self, cr, uid, ids, name, args, context=None):
        res = {}
        for publication in self.browse(cr, uid, ids, context):
            res[publication.id] = len(publication.number_ids)
        return res

    def _get_in_progress_plan(self, cr, uid, ids, name, args, context=None):
        today = time.strftime('%Y-%m-%d')
        res = dict.fromkeys(ids, False)
        for publication in self.browse(cr, uid, ids, context):
            for plan in publication.plan_ids:
                if plan.date_start <= today and (not plan.date_stop or plan.date_stop > today):
                    res[publication.id] = plan.id
        return res

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'issn': fields.char('International Standard Serial Number', size=9, required=True),
        'publisher_id': fields.many2one('res.partner', 'Publisher', required=True, domain=[('supplier', '=', True)], ondelete="restrict"),
        'weight': fields.float('Average Weight', digits_compute=dp.get_precision('Stock Weight'), help="The gross weight in Kg."),
        'country_id': fields.many2one('res.country', 'Country', required=True, ondelete="restrict"),
        'lang_id': fields.many2one('res.lang', 'Languages', required=True, ondelete="restrict"),
        'sale_shop_ids': fields.many2many('sale.shop', 'sale_shop_publication_rel', 'publication_id', 'shop_id', 'Shops',
                                          help="If empty, this publication is available in all shops"),
        'plan_ids': fields.one2many('publication.plan', 'publication_id', 'Publication Plans'),
        'number_ids': fields.one2many('publication.number', 'publication_id', 'Publication Numbers'),
        'number_count': fields.function(_get_number_count, method=True, type='integer', string="Publication Numbers Count"),
        'category_ids': fields.many2many('product.category', 'publication_publication_product_category_rel',
                                         'publication_id', 'category_id', 'Tags'),
        'company_id': fields.many2one('res.company', 'Company', select=True),
        'image': fields.binary("Image", help="This field holds the image used as image for the product, limited to 1024x1024px."),
        'image_url': fields.char('Image URL', size=128),
        'image_small': fields.function(_get_image, fnct_inv=_set_image,
            string="Small-sized image", type="binary",
            store={
                'publication.publication': (lambda self, cr, uid, ids, context=None: ids, ['image', 'image_url'], 10),
            },
            help="Small-sized image of this contact. It is automatically "
                 "resized as a 64x64px image, with aspect ratio preserved. "
                 "Use this field anywhere a small image is required."),
        'has_image': fields.function(_has_image, type="boolean"),
        'date_stop': fields.date('End Date'),
        'plan_in_progress_id': fields.function(_get_in_progress_plan, method=True, type='many2one', relation='publication.plan',
                                               string="Publication plan in progress"),
        'frequency': fields.related('plan_in_progress_id', 'frequency', type='selection', selection=FREQUENCIES,
                                    string='Frequency', readonly=True),
        'active': fields.boolean('Active'),
    }

    def _get_default_company_id(self, cr, uid, context=None):
        return self.pool.get('res.company')._company_default_get(cr, uid, self._name, context=context)

    _defaults = {
        'company_id': _get_default_company_id,
        'active': True,
    }

    _sql_constraints = [
        ('uniq_issn', 'UNIQUE(issn)', 'International Standard Serial Number must be unique'),
    ]

    def copy_data(self, cr, uid, publication_id, default=None, context=None):
        default = default or {}
        default['plan_ids'] = []
        default['number_ids'] = []
        return super(PublicationPublication, self).copy_data(cr, uid, publication_id, default, context)

    def get_publication_numbers(self, cr, uid, ids, date_start=None, date_stop=None, offset=0, limit=None, order=None, context=None, count=False):
        assert not date_start or datetime.strptime(date_start, '%Y-%m-%d'), "date_start must follow the format '%Y-%m-%d'"
        assert not date_stop or datetime.strptime(date_stop, '%Y-%m-%d'), "date_stop must follow the format '%Y-%m-%d'"
        if isinstance(ids, (int, long)):
            ids = [ids]
        domain = [('publication_id', 'in', ids)]
        if date_start:
            domain.append(('publication_date', '>=', date_start))
        if date_stop:
            domain.append(('publication_date', '<=', date_stop))
        return self.pool.get('publication.number').search(cr, uid, domain, offset, limit, order, context, count)


class PublicationPlan(orm.Model):
    _name = 'publication.plan'
    _description = "Publication Plan"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _rec_name = 'date_start'
    _order = 'date_start desc'

    def _get_in_progress(self, cr, uid, ids, name, arg, context=None):
        res = {}.fromkeys(ids, False)
        today = time.strftime('%Y-%m-%d')
        for plan in self.browse(cr, uid, ids, context):
            if plan.date_start <= today and (not plan.date_stop or plan.date_stop > today):
                res[plan.id] = True
        return res

    def _get_publication_days(self, cr, uid, context=None):
        return [(nb, nb) for nb in range(1, 29)]

    _columns = {
        'publication_id': fields.many2one('publication.publication', 'Publication', required=True, ondelete="cascade",
                                          readonly=True, states={'draft': [('readonly', False)]}),
        'create_date': fields.datetime('Creation Date', readonly=True),
        'first_number': fields.integer('First Number', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'date_start': fields.date('Start Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'date_stop': fields.date('End Date', readonly=True),

        'state': fields.selection([('draft', 'Draft'), ('done', 'Validated')], 'State', readonly=True),
        'in_progress': fields.function(_get_in_progress, method=True, type='boolean', string='In progress'),

        'frequency': fields.selection(FREQUENCIES, 'Frequency', required=True, readonly=True, states={'draft': [('readonly', False)]}),

        'january': fields.boolean('January', readonly=True, states={'draft': [('readonly', False)]}),
        'february': fields.boolean('February', readonly=True, states={'draft': [('readonly', False)]}),
        'march': fields.boolean('March', readonly=True, states={'draft': [('readonly', False)]}),
        'april': fields.boolean('April', readonly=True, states={'draft': [('readonly', False)]}),
        'may': fields.boolean('May', readonly=True, states={'draft': [('readonly', False)]}),
        'june': fields.boolean('June', readonly=True, states={'draft': [('readonly', False)]}),
        'july': fields.boolean('July', readonly=True, states={'draft': [('readonly', False)]}),
        'august': fields.boolean('August', readonly=True, states={'draft': [('readonly', False)]}),
        'september': fields.boolean('September', readonly=True, states={'draft': [('readonly', False)]}),
        'october': fields.boolean('October', readonly=True, states={'draft': [('readonly', False)]}),
        'november': fields.boolean('November', readonly=True, states={'draft': [('readonly', False)]}),
        'december': fields.boolean('December', readonly=True, states={'draft': [('readonly', False)]}),
        'publication_day': fields.selection(_get_publication_days, 'Publication Day', readonly=True, states={'draft': [('readonly', False)]}),
        'publication_month': fields.selection([('current', 'Current'), ('previous', 'Previous')], 'Publication Month',
                                              readonly=True, states={'draft': [('readonly', False)]}),

        'monday': fields.boolean('Monday', readonly=True, states={'draft': [('readonly', False)]}),
        'tuesday': fields.boolean('Tuesday', readonly=True, states={'draft': [('readonly', False)]}),
        'wednesday': fields.boolean('Wednesday', readonly=True, states={'draft': [('readonly', False)]}),
        'thursday': fields.boolean('Thursday', readonly=True, states={'draft': [('readonly', False)]}),
        'friday': fields.boolean('Friday', readonly=True, states={'draft': [('readonly', False)]}),
        'saturday': fields.boolean('Saturday', readonly=True, states={'draft': [('readonly', False)]}),
        'sunday': fields.boolean('Sunday', readonly=True, states={'draft': [('readonly', False)]}),
        'weeks': fields.integer('Weeks between publication numbers', readonly=True, states={'draft': [('readonly', False)]}),

        'stand_price_paper': fields.float('Stand Price - Paper', digits_compute=dp.get_precision('Product Price'), required=True,
                                          readonly=True, states={'draft': [('readonly', False)]}),
        'stand_price_digital': fields.float('Stand Price - Digital', digits_compute=dp.get_precision('Product Price'), required=True,
                                            readonly=True, states={'draft': [('readonly', False)]}),
        'publisher_price_paper': fields.float('Publisher Price - Paper', digits_compute=dp.get_precision('Product Price'), required=True,
                                              readonly=True, states={'draft': [('readonly', False)]}),
        'publisher_price_digital': fields.float('Publisher Price - Digital', digits_compute=dp.get_precision('Product Price'), required=True,
                                                readonly=True, states={'draft': [('readonly', False)]}),
        'commission_rate_paper': fields.float('Commission rate - Paper', digits_compute=dp.get_precision('Product Price'), required=True,
                                              readonly=True, states={'draft': [('readonly', False)]}),
        'commission_rate_digital': fields.float('Commission rate - Digital', digits_compute=dp.get_precision('Product Price'), required=True,
                                                readonly=True, states={'draft': [('readonly', False)]}),
    }

    _defaults = {
        'state': 'draft',
        'date_start': lambda *a: time.strftime('%Y-%m-%d'),
        'first_number': 1,
        'publication_day': 1,
        'publication_month': 'current',
        'weeks': 1,
    }

    def _check_commission_rates(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for plan in self.browse(cr, uid, ids, context):
            for commission_rate_field in ('commission_rate_paper', 'commission_rate_digital'):
                commission_rate = getattr(plan, commission_rate_field)
                if commission_rate < 0.0 or commission_rate > 100.0:
                    return False
        return True

    _constraints = [
        (_check_commission_rates, 'Commission Rates must be between 0.0 and 100.0', ['commission_rate_paper', 'commission_rate_digital']),
    ]

    def write(self, cr, uid, ids, vals, context=None):
        if 'date_stop' in vals:
            cr.execute('DELETE FROM publication_number WHERE plan_id IN %s AND publication_date > %s', (tuple(ids), vals['date_stop']))
        return super(PublicationPlan, self).write(cr, uid, ids, vals, context)

    def button_validate(self, cr, uid, ids, context=None):
        today = time.strftime('%Y-%m-%d')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for plan in self.browse(cr, uid, ids, context):
            if plan.date_start < today:
                raise orm.except_orm(_('Error'), _('Start date must be in the future'))
            old_plan_ids = self.search(cr, uid, [
                ('id', '!=', plan.id),
                ('publication_id', '=', plan.publication_id.id),
                ('date_start', '<=', plan.date_start),
                '|',
                    ('date_stop', '>', plan.date_start),
                    ('date_stop', '=', False),
            ], limit=1, context=context)
            if old_plan_ids:
                old_plan = self.browse(cr, uid, old_plan_ids[0], context)
                if old_plan.date_stop:
                    plan.write({'date_stop': old_plan.date_stop})
                old_plan.write({'date_stop': plan.date_start})
        self.generate_publication_numbers(cr, uid, ids, context=None)
        self.write(cr, uid, ids, {'state': 'done'}, context)
        return {'type': 'ir.actions.act_window_close'}

    def generate_publication_numbers(self, cr, uid, ids, context=None):
        number_obj = self.pool.get('publication.number')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for plan in self.browse(cr, uid, ids, context):
            number = plan.first_number
            next_publication_dates = self._get_next_publication_dates(cr, uid, plan, context)
            for index, publication_date in enumerate(next_publication_dates):
                date_stop = False
                if index < len(next_publication_dates) - 1:
                    date_stop = next_publication_dates[index + 1]
                number_obj.create(cr, uid, {
                    'publication_id': plan.publication_id.id,
                    'plan_id': plan.id,
                    'number': number,
                    'publication_date': publication_date,
                    'date_start': publication_date,
                    'date_stop': date_stop,
                }, context)
                number += 1
        return True

    def _get_next_publication_dates(self, cr, uid, plan, context=None):
        res = []
        date_start = datetime.strptime(plan.date_start, '%Y-%m-%d')
        date_stop = date_start + relativedelta(years=2)
        plan_date_stop = plan.date_stop and datetime.strptime(plan.date_stop, '%Y-%m-%d') or date_stop
        date_stop = min(date_stop, plan_date_stop)
        publication_date = date_start
        if plan.frequency == 'monthly':
            for year in range(date_start.year, date_start.year + 2):
                for index, month in enumerate(MONTHS):
                    if getattr(plan, month):
                        publication_date += relativedelta(day=plan.publication_day, month=index + 1, year=year)
                        if publication_date > date_stop:
                            break
                        if publication_date < date_start:
                            continue
                        res.append(publication_date.strftime('%Y-%m-%d'))
        elif plan.frequency == 'daily':
            if publication_date.weekday():
                publication_date += relativedelta(weekday=dateutil.relativedelta.MO, days=-7)
            for week in range(105):
                if week % plan.weeks:
                    if not publication_date.weekday():
                        publication_date += relativedelta(days=7)
                    else:
                        publication_date += relativedelta(weekday=dateutil.relativedelta.MO)
                else:
                    for index, day in enumerate(DAYS):
                        monday = publication_date
                        if monday.weekday():
                            monday += relativedelta(weekday=dateutil.relativedelta.MO)
                        if getattr(plan, day):
                            publication_date = monday + relativedelta(days=index)
                            if publication_date > date_stop:
                                break
                            if publication_date < date_start:
                                continue
                            res.append(publication_date.strftime('%Y-%m-%d'))
        return sorted(res)

    def copy_data(self, cr, uid, plan_id, default=None, context=None):
        default = default or {}
        default['number_ids'] = []
        return super(PublicationPlan, self).copy_data(cr, uid, plan_id, default, context)


def create_unique_index(original_load):
    @wraps(original_load)
    def wrapper(self, cr, module):
        """Add constraint in order to ban several active publication numbers with a same number"""
        res = original_load(self, cr, module)
        cr.execute("SELECT indexname FROM pg_indexes WHERE indexname = 'publication_number_unique_number_index'")
        if not cr.fetchall():
            cr.execute("CREATE UNIQUE INDEX publication_number_unique_number_index "
                       "ON publication_number (publication_id, number) WHERE active")
        return res
    return wrapper


class PublicationNumber(orm.Model):
    _name = "publication.number"
    _description = "Publication Number"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _rec_name = "number"
    _order = "publication_date desc"

    def __init__(self, pool, cr):
        super(PublicationNumber, self).__init__(pool, cr)
        cr.execute("SELECT relname FROM pg_class WHERE relname=%s", (self._table,))
        if cr.fetchall():
            setattr(Registry, 'load', create_unique_index(getattr(Registry, 'load')))

    def _has_image(self, cr, uid, ids, name, args, context=None):
        res = {}
        for number in self.browse(cr, uid, ids, context):
            res[number.id] = bool(number.image)
        return res

    def _get_image(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for number in self.browse(cr, uid, ids, context):
            res[number.id] = image_get_resized_images(number.image)
        return res

    def _set_image(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'image': image_resize_image_big(value)}, context=context)

    def _get_publication_info(self, cr, uid, ids, name, args, context=None):
        res = {}
        for number in self.browse(cr, uid, ids, context):
            res[number.id] = {
                'publisher_id': number.publication_id.publisher_id.id,
                'country_id': number.publication_id.country_id.id,
                'lang_id': number.publication_id.lang_id.id,
            }
        return res

    def _get_number_ids_from_publications(self, cr, uid, ids, context=None):
        return [number.id for publication in self.browse(cr, uid, ids, context) for number in publication.number_ids]

    _columns = {
        'publication_id': fields.many2one('publication.publication', 'Publication', required=True, ondelete="cascade"),
        'plan_id': fields.many2one('publication.plan', 'Publication plan', required=True, ondelete="cascade"),
        'number': fields.char('Number', size=12, required=True),
        'publication_date': fields.date('Publication Date', required=True),
        'product_ids': fields.one2many('product.product', 'publication_number_id', 'Products'),
        'active': fields.boolean("Active"),

        'date_start': fields.date('Start Date'),
        'date_stop': fields.date('End Date'),

        'image': fields.binary("Image", help="This field holds the image used as image for the product, limited to 1024x1024px."),
        'image_small': fields.function(_get_image, fnct_inv=_set_image,
            string="Small-sized image", type="binary", multi="_get_image",
            store={
                'publication.number': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Small-sized image of this contact. It is automatically "
                 "resized as a 64x64px image, with aspect ratio preserved. "
                 "Use this field anywhere a small image is required."),
        'has_image': fields.function(_has_image, type="boolean"),

        'issn': fields.related('publication_id', 'issn', type='char', string="International Standard Serial Number", readonly=True),
        'country_id': fields.function(_get_publication_info, method=True, type='many2one', relation='res.country', string="Country", store={
            'publication.publication': (_get_number_ids_from_publications, ['country_id'], 10),
        }, multi='publication'),
        'lang_id': fields.function(_get_publication_info, method=True, type='many2one', relation='res.lang', string="Language", store={
            'publication.publication': (_get_number_ids_from_publications, ['lang_id'], 10),
        }, multi='publication'),
        'publisher_id': fields.function(_get_publication_info, method=True, type='many2one', relation='res.partner', string="Publisher", store={
            'publication.publication': (_get_number_ids_from_publications, ['publisher_id'], 10),
        }, multi='publication'),
        'analytic_line_ids': fields.one2many('account.analytic.line', 'publication_number_id', 'Analytic Lines'),
    }

    _defaults = {
        'active': True,
    }

    def onchange_publication(self, cr, uid, ids, publication_id, plan_id, context=None):
        res = {'value': {}}
        if publication_id and plan_id and self.pool.get('publication.plan').browse(cr, uid, plan_id, context).publication_id.id != publication_id:
            res['value']['plan_id'] = False
        return res

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        lang = self.pool.get('res.users').browse(cr, uid, uid, context).lang
        cr.execute('SELECT date_format FROM res_lang WHERE code = %s', (lang,))
        date_format = cr.fetchall()[0][0]
        for number in self.browse(cr, uid, ids, context):
            publication_date = datetime.strptime(number.publication_date, '%Y-%m-%d')
            if number.plan_id.frequency == 'monthly':
                publication_date = "%s %s" % (_(publication_date.strftime("%B")), publication_date.strftime("%Y"))
            if number.plan_id.frequency == 'daily':
                publication_date = publication_date.strftime(date_format)
            name = u'%s n°%s - %s' % (number.publication_id.name, number.number, publication_date)
            res.append((number.id, name))
        return res

    def button_delete(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        context['default_publication_number_id'] = ids[0]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Publication Number Deletion'),
            'res_model': 'publication.number.deletion_wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }

    def copy_data(self, cr, uid, number_id, default=None, context=None):
        default = default or {}
        default['product_ids'] = []
        default['analytic_line_ids'] = []
        return super(PublicationNumber, self).copy_data(cr, uid, number_id, default, context)

    def unlink(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        product_ids = []
        analytic_line_ids = []
        for number in self.browse(cr, uid, ids, context):
            product_ids.extend([product.id for product in number.product_ids])
            analytic_line_ids.extend([line.id for line in number.analytic_line_ids])
        self.pool.get('product.product').write(cr, uid, product_ids, {'active': False}, context)
        self.pool.get('account.analytic.line').unlink(cr, uid, analytic_line_ids, context)
        return self.write(cr, uid, ids, {'active': False}, context)
