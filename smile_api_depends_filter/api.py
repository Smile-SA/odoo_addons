# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api
from odoo.api import attrsetter


def depends(*args):
    """ Return a decorator that specifies the field dependencies of a "compute"
        method (for new-style function fields). Each argument must be a string
        that consists in a dot-separated sequence of field names::

            pname = fields.Char(compute='_compute_pname')

            @api.one
            @api.depends('partner_id.name', 'partner_id.is_company')
            def _compute_pname(self):
                if self.partner_id.is_company:
                    self.pname = (self.partner_id.name or "").upper()
                else:
                    self.pname = self.partner_id.name

        One may also pass a single function as argument. In that case, the
        dependencies are given by calling the function with the field's model.
    """
    if args and callable(args[0]):
        args = args[0]
    elif any('id' in (arg[0].split('.') if isinstance(
                arg, tuple) else arg.split('.')) for arg in args):
        raise NotImplementedError(
            "Compute method cannot depend on field 'id'.")
    return attrsetter('_depends', args)


api.depends = depends
