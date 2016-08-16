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

from openerp import api, fields, models, tools


class AbstractLog(models.AbstractModel):
    """
        This is an abstract model for common attributes and features of logs.
        Please complete these fields on models inheriting AbstractLog:

        build_id = fields.Many2one(ondelete='cascade')
        branch_id = fields.Many2one(store=True)
    """
    _name = 'scm.repository.branch.build.abstract.log'
    _description = 'Log'

    create_date = fields.Datetime('Created on', readonly=True)
    module = fields.Char(readonly=True)
    file = fields.Char(readonly=True)
    build_id = fields.Many2one('scm.repository.branch.build', 'Build', readonly=True, required=True, index=True)
    branch_id = fields.Many2one('scm.repository.branch', 'Branch', readonly=True, related='build_id.branch_id', store=False)

    @api.model
    def _get_logs_to_purge(self, date):
        return self.search([('create_date', '<=', date)])

    @api.model
    def purge(self, date):
        logs = self._get_logs_to_purge(date)
        return logs.unlink()


class Log(models.Model):
    _name = 'scm.repository.branch.build.log'
    _description = 'Log'
    _inherit = 'scm.repository.branch.build.abstract.log'
    _rec_name = 'file'
    _order = 'id desc'

    @api.one
    def _get_exception_short(self):
        self.exception_short = self.exception and tools.html2plaintext(self.exception[:101]) or ''

    build_id = fields.Many2one(ondelete='cascade')
    branch_id = fields.Many2one(store=True)
    type = fields.Selection([
        ('quality_code', 'Quality code'),
        ('test', 'Test')
    ], required=True, readonly=True)
    result = fields.Selection([
        ('error', 'Error'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('ignored', 'Ignored')
    ], required=True, readonly=True)
    line = fields.Integer(readonly=True, group_operator="count")
    code = fields.Char('Class', readonly=True, required=True)
    exception = fields.Html('Exception', readonly=True)
    duration = fields.Float('Duration', digits=(7, 3), help='In seconds', readonly=True)
    exception_short = fields.Char('Exception', compute='_get_exception_short')

    @api.one
    def name_get(self):
        return (self.id, '%s/%s' % (self.module, self.file))


class Coverage(models.Model):
    _name = 'scm.repository.branch.build.coverage'
    _description = 'Code Coverage'
    _inherit = 'scm.repository.branch.build.abstract.log'
    _rec_name = 'file'
    _order = 'id desc'

    build_id = fields.Many2one(ondelete='cascade')
    branch_id = fields.Many2one(store=True)
    line_count = fields.Integer('# lines', readonly=True)
    line_rate = fields.Float('Lines rate', digits=(5, 2), readonly=True)
    branch_count = fields.Integer('# conditionals', readonly=True)
    branch_rate = fields.Float('Conditionals rate', digits=(5, 2), readonly=True)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        fields_to_compute = []
        for field in ('line_rate', 'branch_rate'):
            if field in fields:
                fields.remove(field)
                fields_to_compute.append(field)
        res = super(Coverage, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)
        if fields_to_compute:
            fields_to_read = ['line_count', 'branch_count', 'branch_rate', 'line_rate']
            for group in res:
                if group.get('__domain'):
                    line_infos = self.search_read(group['__domain'], fields_to_read)
                    line_counts = sum([l['line_count'] for l in line_infos])
                    branch_counts = sum([l['branch_count'] for l in line_infos])
                    group['line_rate'] = line_counts and \
                        sum([l['line_rate'] * l['line_count'] for l in line_infos]) / line_counts or 0
                    group['branch_rate'] = branch_counts and \
                        sum([l['branch_rate'] * l['branch_count'] for l in line_infos]) / branch_counts or 0
        return res
