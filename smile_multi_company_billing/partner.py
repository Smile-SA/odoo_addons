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

from osv import osv, fields


class ResPartner(osv.osv):
    _inherit = "res.partner"

    def _get_partner_company(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        for partner_id in ids:
            res[partner_id] = {'is_intragroup_company': False, 'partner_company_id': False}
        company_obj = self.pool.get('res.company')
        company_ids = company_obj.search(cr, uid, [], context=context)
        for company in company_obj.read(cr, uid, company_ids, ['partner_id'], context, '_classic_write'):
            if company['partner_id'] in ids:
                res[company['partner_id']] = {'is_intragroup_company': True, 'partner_company_id': company['id']}
        return res

    def _get_partner_ids_from_company(self, cr, uid, ids, context=None):
        return [company.partner_id.id for company in self.browse(cr, uid, ids, context)]

    _columns = {
        'is_intragroup_company': fields.function(_get_partner_company, method=True, type='boolean', store={
            'res.company': (_get_partner_ids_from_company, ['partner_id'], 10),
        }, string='Is an intra-group company', multi='intragroup'),
        'partner_company_id': fields.function(_get_partner_company, method=True, type='many2one', relation="res.company", store={
            'res.company': (_get_partner_ids_from_company, ['partner_id'], 10),
        }, string='Company', multi='intragroup'),
    }

    def create(self, cr, uid, vals, context=None):
        res_id = super(ResPartner, self).create(cr, uid, vals, context)
        self._store_set_values(cr, uid, [res_id], ['is_intragroup_company', 'partner_company_id'], context)
        return res_id
ResPartner()
