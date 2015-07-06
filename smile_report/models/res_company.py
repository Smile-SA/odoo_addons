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


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _get_rml_footer(self):
        return []

    custom_header = fields.Boolean('Use image as a header')
    header_image = fields.Binary(help='Image used as header on reports')

    @api.onchange('custom_footer')
    def _onchange_footer(self):
        if not self.custom_footer:
            rml_footer = self._get_rml_footer()
            self.rml_footer = '<br/>\n'.join(rml_footer)

    @api.multi
    def preview_report(self):
        """Print a demo report based on the current company"""
        self.ensure_one()
        report_type = self._context.get('report_type', 'pdf')
        if report_type not in ('html', 'pdf'):
            return
        return {
            'name': _('Report preview'),
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/report/%s/smile_report.demo_report_document/%s' % (report_type, self.id),
        }
