# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from lxml import etree

from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval


class ResPartner(models.Model):
    _inherit = 'res.partner'

    parent_id = fields.Many2one(ondelete='restrict')
    type = fields.Selection(default=False)
    partner_type_id = fields.Many2one('res.partner.type', 'Partner Type')
    can_have_parent = fields.Boolean(compute='_get_partner_type_infos')
    parent_is_required = fields.Boolean(compute='_get_partner_type_infos')
    parent_type_ids = fields.Many2many(
        'res.partner.type', string='Company types authorized for parent',
        compute='_get_parent_types')
    contact_ids = fields.One2many(
        'res.partner', 'parent_id', 'Contacts & Addresses',
        domain=[('is_company', '=', False)])
    subcompanies_count = fields.Integer(
        'Number of sub-companies', compute='_count_subcompanies')
    subcompanies_label = fields.Char(
        related='partner_type_id.subcompanies_label', readonly=True)
    parent_relation_label = fields.Char(
        related='partner_type_id.parent_relation_label', readonly=True)
    customer = fields.Boolean(string='Is a Customer', default=True,
                              help="Check this box if this contact is a customer. It can be selected in sales orders.")
    supplier = fields.Boolean(string='Is a Vendor',
                              help="Check this box if this contact is a vendor. It can be selected in purchase orders.")

    @api.depends('partner_type_id')
    def _get_parent_types(self):
        self.parent_type_ids = self.partner_type_id.parent_type_ids

    @api.depends('child_ids')
    def _count_subcompanies(self):
        subcompanies = self.mapped('child_ids').filtered(
            lambda child: child.is_company)
        self.subcompanies_count = len(subcompanies)

    @api.depends('partner_type_id')
    def _get_partner_type_infos(self):
        self.can_have_parent = True
        self.parent_is_required = False
        if self.partner_type_id:
            self.can_have_parent = self.partner_type_id.can_have_parent
            if self.partner_type_id.can_have_parent:
                self.parent_is_required = \
                    self.partner_type_id.parent_is_required

    @api.onchange('company_type')
    def _onchange_company_type(self):
        code = 'CONTACT'
        if self.company_type == 'company':
            code = 'SUPPLIER' if self.supplier else 'CLIENT'
        self.partner_type_id = self.partner_type_id.search(
            [('code', '=', code)], limit=1)

    @api.onchange('partner_type_id')
    def _onchange_partner_type(self):
        self.update(self._get_inherit_values(self.partner_type_id))

    def _get_inherit_values(self, partner_type, not_null=False):
        if not partner_type:
            return {}
        inherit_fields = getattr(
            partner_type, '_%s_inherit_fields' % partner_type.company_type)
        inherit_values = partner_type.read(inherit_fields)[0]
        if 'id' in inherit_values:
            del inherit_values['id']
        if not_null:
            for fname in list(inherit_values.keys()):
                if not inherit_values[fname]:
                    del inherit_values[fname]
        return inherit_values

    def _update_children(self, vals):
        for partner in self:
            if partner.child_ids and partner.partner_type_id.field_ids:
                children_vals = {
                    key: value for key, value in vals.items()
                    if key in partner.partner_type_id.field_ids.mapped('name')}
                if children_vals:
                    partner.child_ids.write(children_vals)

    @api.model
    def create(self, vals):
        partner_type = self.env['res.partner.type'].browse(
            vals.get('partner_type_id'))
        vals.update(self._get_inherit_values(partner_type))
        new_partner = super(ResPartner, self).create(vals)
        new_partner._update_children(vals)
        return new_partner

    def write(self, vals):
        partners_by_type = {}
        if vals.get('partner_type_id'):
            partner_type = self.env['res.partner.type'].browse(
                vals['partner_type_id'])
            partners_by_type[partner_type] = self
        else:
            for partner in self:
                partners_by_type.setdefault(
                    partner.partner_type_id, self.browse())
                partners_by_type[partner.partner_type_id] |= partner
        for partner_type in partners_by_type:
            if list(vals.keys()) != ['is_company']:  # To avoid infinite loop
                vals.update(self._get_inherit_values(
                    partner_type, not_null=True))
            super(ResPartner, partners_by_type[partner_type]).write(vals)
        self._update_children(vals)
        return True

    def view_subcompanies(self):
        return {
            'name': _('Sub-companies'),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'tree,form',
            'view_id': False,
            'domain': [
                ('parent_id', 'in', self.ids),
                ('is_company', '=', True)
            ],
            'target': 'current',
        }

    def _update_fields_view_get_result(self, result, view_type='form'):
        if view_type == 'form' and not self._context.get(
                'display_original_view'):
            # In order to inherit all views based on the field order_line
            doc = etree.XML(result['arch'])
            for node in doc.xpath("//field[@name='child_ids']"):
                node.set('name', 'contact_ids')
                node.set('modifiers', json.dumps(
                    {'default_customer': False, 'default_supplier': False}))
                result['fields']['contact_ids'] = result['fields']['child_ids']
                result['fields']['contact_ids'].update(
                    self.fields_get(['contact_ids'])['contact_ids'])
            result['arch'] = etree.tostring(doc)
        return result

    @api.model
    def fields_view_get(
            self, view_id=None, view_type='form',
            toolbar=False, submenu=False):
        res = super(ResPartner, self).fields_view_get(
            view_id, view_type, toolbar, submenu)
        return self._update_fields_view_get_result(res, view_type)

    @api.model
    def _format_args(self, args):
        for cond in (args or []):
            if len(cond) == 3 and cond[2] and isinstance(cond[2], list) and \
                    isinstance(cond[2][0], list):
                for index, item in enumerate(cond[2]):
                    if item[0] == 1:
                        cond[2][index] = item[1]
                    elif item[0] == 6:
                        cond[2] = item[2]
                        break

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        self._format_args(args)
        return super(ResPartner, self).name_search(name, args, operator, limit)

    @api.model
    def _search(
            self, args, offset=0, limit=None, order=None, count=False,
            access_rights_uid=None):
        self._format_args(args)
        return super(ResPartner, self)._search(
            args, offset, limit, order, count, access_rights_uid)

    def _get_display_name_context(self):
        self.ensure_one()
        partner = self.with_context(
            show_address=None, show_address_only=None, show_email=None)
        return {'partner': partner, '_': _}

    @api.depends('partner_type_id.partner_display_name')
    def _compute_display_name(self):
        rule = self.partner_type_id.partner_display_name
        if rule:
            self.display_name = safe_eval(
                rule, self._get_display_name_context())
        else:
            super(ResPartner, self)._compute_display_name()
