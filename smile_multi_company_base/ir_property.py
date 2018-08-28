# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Smile (<http://www.smile.fr>).
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

from base.res.ir_property import ir_property


def new_get_domain(self, cr, uid, prop_name, model, context=None):
    context = context or {}
    if not isinstance(prop_name, (list, tuple)):
        prop_name = [prop_name]
    # Accept a list of properties
    cr.execute('select id from ir_model_fields where name in %s and model=%s', (tuple(prop_name), model))
    res = cr.fetchone()
    if not res:
        return None

    if context.get('force_company'):
        cid = context['force_company']
    else:
        company = self.pool.get('res.company')
        cid = company._company_default_get(cr, uid, model, res[0], context=context)

    domain = ['&', ('fields_id', '=', res[0]),
              '|', ('company_id', '=', cid), ('company_id', '=', False)]
    return domain

ir_property._get_domain = new_get_domain
