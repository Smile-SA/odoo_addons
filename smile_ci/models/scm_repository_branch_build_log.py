# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


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
    build_id = fields.Many2one(
        'scm.repository.branch.build', 'Build', readonly=True,
        required=True, index=True)
    branch_id = fields.Many2one(
        'scm.repository.branch', related='build_id.branch_id', readonly=True)

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
        self.exception_short = self.exception and tools.html2plaintext(
            self.exception[:101]) or ''

    build_id = fields.Many2one(ondelete='cascade')
    branch_id = fields.Many2one(store=True)
    type = fields.Selection([
        ('quality_code', 'Code quality'),
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
    duration = fields.Float('Duration', digits=(
        7, 3), help='In seconds', readonly=True)
    exception_short = fields.Char('Exception', compute='_get_exception_short')

    @api.one
    def name_get(self):
        return (self.id, '%s/%s' % (self.module, self.file))
