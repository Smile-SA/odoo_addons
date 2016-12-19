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

from lxml import etree

from openerp import api, fields, models, _
from openerp.exceptions import UserError, ValidationError

from openerp.addons.smile_product_option.models.product import QUANTITY_TYPES


class ProductOptionOrder(models.AbstractModel):
    _name = 'product.option.order'
    _description = 'Product Option Order'
    _order_line_field = ''

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(ProductOptionOrder, self).fields_view_get(view_id, view_type, toolbar, submenu)
        if view_type == 'form' and not self._context.get('display_original_view'):
            # In order to inherit all views based on the field order_line
            doc = etree.XML(result['arch'])
            for node in doc.xpath("//field[@name='%s']" % self._order_line_field):
                node.set('name', 'visible_line_ids')
            result['arch'] = etree.tostring(doc)
            result['fields']['visible_line_ids'] = result['fields'][self._order_line_field]
        return result

    @api.multi
    def _get_lines_max_level(self):
        parents = self[self._order_line_field].filtered(lambda line: not line.parent_id)
        max_level = 0
        children = parents.mapped('child_ids')
        while children:
            max_level += 1
            children = children.mapped('child_ids')
        return max_level

    @api.one
    def _update_lines_sequence(self):
        def update_sequence(lines, level, parent_sequence):
            for index, line in enumerate(lines):
                new_sequence = parent_sequence + (index + 1) * 100 ** level
                if line.sequence != new_sequence:
                    line.sequence = new_sequence

        level = self._get_lines_max_level()
        parents = self[self._order_line_field].filtered(lambda line: not line.parent_id)
        update_sequence(parents, level, 0)
        while level > 0:
            level -= 1
            for parent in parents:
                update_sequence(parent.child_ids, level, parent.sequence)
            parents = parents.mapped('child_ids')

    @api.multi
    def write(self, vals):
        res = super(ProductOptionOrder, self).write(vals)
        for line_tuple in (vals.get('visible_line_ids') or []):
            # If a line is created or its sequence is updated,
            # I recompute the sequence for all order lines
            if not line_tuple[0] or \
                    (line_tuple[0] == 1 and 'sequence' in (line_tuple[2] or {})):
                self._update_lines_sequence()
                break
        return res


class ProductOptionOrderLine(models.AbstractModel):
    _name = 'product.option.order.line'
    _description = 'Product Option Order Line'
    _order_field = ''
    _qty_field = ''
    _uom_field = ''

    @api.one
    @api.depends('price_unit', 'child_ids.price_unit')
    def _compute_visible_price(self):
        hidden_children = self.child_ids.filtered(lambda child: child.is_hidden)
        self.visible_price_unit = self.price_unit + sum(hidden_children.mapped('price_unit'))
        self.visible_price_subtotal = self.price_subtotal + sum(hidden_children.mapped('price_subtotal'))

    @api.one
    def _set_visible_price_unit(self):
        children_included_in_price = self.child_ids.filtered(lambda child: child.is_included_in_price)
        self.price_unit = self.visible_price_unit - sum(children_included_in_price.mapped('price_unit'))

    parent_id = fields.Many2one('product.option.order.line', 'Main Line', ondelete='cascade', copy=False)
    child_ids = fields.One2many('product.option.order.line', 'parent_id', string='Options', context={'active_test': False})
    quantity_type = fields.Selection(QUANTITY_TYPES, readonly=True)
    is_mandatory = fields.Boolean('Is a mandatory option', readonly=True)
    is_included_in_price = fields.Boolean(readonly=True)
    is_hidden = fields.Boolean(readonly=True)
    visible_price_unit = fields.Monetary(compute='_compute_visible_price', string='Unit Price',
                                         inverse='_set_visible_price_unit', store=True)
    visible_price_subtotal = fields.Monetary(compute='_compute_visible_price', string='Subtotal',
                                             readonly=True, store=True)
    # The following fields are specified here just to allow to define visible_price_unit and visible_price_subtotal
    currency_id = fields.Many2one('res.currency', 'Currency')
    price_unit = fields.Monetary('Unit Price')
    price_subtotal = fields.Monetary('Subtotal')

    @api.one
    def _check_qty(self):
        if self.quantity_type == 'identical' and \
                self[self._qty_field] != self.parent_id[self._qty_field]:
            raise ValidationError(_('The option %s must be the same in quantity as the product %s')
                                  % (self.product_id.name, self.parent_id.product_id.name))
        if self.quantity_type == 'free_and_multiple' and \
                self[self._qty_field] % self.parent_id[self._qty_field]:
            raise ValidationError(_('The option %s must be a multiple of the product %s')
                                  % (self.product_id.name, self.parent_id.product_id.name))

    @api.multi
    def _get_option_vals(self, option):
        self.ensure_one()
        qty = 0.0
        if option.quantity_type == 'fixed':
            qty = option.fixed_quantity
        elif option.quantity_type == 'identical':
            qty = self[self._qty_field]
        return {
            self._order_field: self[self._order_field].id,
            'parent_id': self.id,
            'product_id': option.optional_product_id.id,
            self._qty_field: qty,
            self._uom_field: option.uom_id.id,
            'quantity_type': option.quantity_type,
            'is_mandatory': option.is_mandatory,
            'is_included_in_price': option.is_included_in_price,
        }

    @api.multi
    def _update_optional_lines(self):
        for line in self:
            options = line.product_id.product_tmpl_id.option_ids
            # Remove wrong option lines
            wrong_option_lines = line.child_ids.filtered(lambda child: child.product_id not in
                                                         options.mapped('optional_product_id'))
            if wrong_option_lines:
                line.with_context(force_unlink=True).child_ids -= wrong_option_lines
            # Create new option lines
            for option in options:
                if self._context.get('add_all_options') or option.is_mandatory:
                    option_line = line.child_ids.filtered(lambda child: child.product_id ==
                                                          option.optional_product_id)
                    if not option_line:
                        self.create(line._get_option_vals(option))

    @api.one
    def _update_unit_price(self):
        # Because the unit price of an option included in price is read-only
        if self.is_included_in_price:
            self.parent_id.price_unit -= self.price_unit

    @api.model
    def create(self, vals):
        line = super(ProductOptionOrderLine, self).create(vals)
        if not self._context.get('do_not_update_optional_lines'):
            line._update_unit_price()
            line._update_optional_lines()
        return line

    @api.multi
    def _update_optional_lines_qty(self):
        for parent in self:
            options = parent.child_ids.filtered(lambda child: child.quantity_type == 'identical' and
                                                child[self._qty_field] != parent[self._qty_field])
            if options:
                options.write({self._qty_field: parent[self._qty_field]})

    @api.multi
    def _check_vals(self, vals):
        if 'price_unit' in vals and \
                self.filtered(lambda line: line.is_included_in_price):
            raise UserError(_('You cannot change the unit price of an option '
                              'included in the price of the main product'))

    @api.multi
    def write(self, vals):
        self._check_vals(vals)
        res = super(ProductOptionOrderLine, self).write(vals)
        if 'product_id' in vals:
            self._update_optional_lines()
        if self._qty_field in vals:
            self._update_optional_lines_qty()
        return res

    @api.multi
    def unlink(self):
        parents = self
        while parents:
            children = parents.mapped('child_ids')
            self |= children
            parents = children
        if not self._context.get('force_unlink') and any(self.mapped('is_mandatory')):
            parents = self.filtered(lambda line: line.is_mandatory).mapped('parent_id')
            if len(parents & self) != len(parents):
                raise Warning(_("You cannot delete a mandatory option!"))
        return super(ProductOptionOrderLine, self).unlink()
