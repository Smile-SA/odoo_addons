# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
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

from dateutil.relativedelta import relativedelta

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    version_ids = fields.One2many('product.pricelist.version', 'pricelist_id', 'Pricelist versions')

    @api.multi
    def _get_default_version_vals(self):
        self.ensure_one()
        return {
            'name': _('Default version'),
            'pricelist_id': self.id,
            'item_ids': [(6, 0, self.item_ids.ids)] if self.item_ids else False,
        }

    @api.model
    def create(self, vals):
        pricelist = super(ProductPricelist, self).create(vals)
        if not vals.get('version_ids') and not self._context.get('do_not_create_default_version'):
            version_vals = pricelist._get_default_version_vals()
            self.env['product.pricelist.version'].create(version_vals)
        return pricelist


class ProductPricelistVersion(models.Model):
    _name = 'product.pricelist.version'
    _description = 'Pricelist Version'
    _order = 'date_start desc'

    name = fields.Char(required=True, translate=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', required=True,
                                   ondelete='cascade', auto_join=True)
    item_ids = fields.One2many('product.pricelist.item', 'version_id', 'Pricelist items')
    date_start = fields.Date('Start date', copy=False)
    date_end = fields.Date('End date', copy=False)

    @api.one
    @api.constrains('date_start', 'date_end')
    def _check_date(self):
        where = []
        if self.date_start:
            where.append("((date_end>='%s') or (date_end is null))" % (self.date_start,))
        if self.date_end:
            where.append("((date_start<='%s') or (date_start is null))" % (self.date_end,))
        query = "SELECT id FROM product_pricelist_version WHERE pricelist_id = %s AND id <> %s"
        if where:
            query += " AND " + " AND ".join(where)
        self._cr.execute(query, (self.pricelist_id.id, self.id))
        if self._cr.fetchall():
            raise ValidationError(_('You cannot have 2 pricelist versions that overlap!'))

    @api.one
    def copy_data(self, default=None):
        vals = super(ProductPricelistVersion, self).copy_data(default)
        if self.date_end:
            date_end = fields.Date.from_string(self.date_end)
            date_start = date_end + relativedelta(days=+1)
            vals['date_start'] = date_start
        return vals


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'
    _order = "applied_on, sequence, min_quantity desc, categ_id desc"  # add sequence on order

    version_id = fields.Many2one('product.pricelist.version', 'Pricelist version',
                                 required=True, ondelete='cascade', auto_join=True)
    date_start = fields.Date(related='version_id.date_start', store=True, readonly=True)
    date_end = fields.Date(related='version_id.date_end', store=True, readonly=True)

    @api.model
    def create(self, vals):
        if 'version_id' not in vals:
            pricelist = self.env['product.pricelist'].browse(vals['pricelist_id'])
            # Because versions are ordered by date_start desc
            vals['version_id'] = pricelist.version_ids and pricelist.version_ids.ids[0] or False
        return super(ProductPricelistItem, self).create(vals)
