# -*- coding: utf-8 -*-

from odoo import api, fields, models


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
    branch_rate = fields.Float(
        'Conditionals rate', digits=(5, 2), readonly=True)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None,
                   orderby=False, lazy=True):
        fields_to_compute = []
        for field in ('line_rate', 'branch_rate'):
            if field in fields:
                fields.remove(field)
                fields_to_compute.append(field)
        res = super(Coverage, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)
        if fields_to_compute:
            fields_to_read = ['line_count',
                              'branch_count', 'branch_rate', 'line_rate']
            for group in res:
                if group.get('__domain'):
                    line_infos = self.search_read(
                        group['__domain'], fields_to_read)
                    line_counts = sum([l['line_count'] for l in line_infos])
                    branch_counts = sum([l['branch_count']
                                         for l in line_infos])
                    group['line_rate'] = line_counts and \
                        sum([l['line_rate'] * l['line_count']
                             for l in line_infos]) / line_counts or 0
                    group['branch_rate'] = branch_counts and \
                        sum([l['branch_rate'] * l['branch_count']
                             for l in line_infos]) / branch_counts or 0
        return res
