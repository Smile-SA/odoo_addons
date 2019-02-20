# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError

LICENSES = [
    ('GPL-2', 'GPL Version 2'),
    ('GPL-2 or any later version', 'GPL-2 or later version'),
    ('GPL-3', 'GPL Version 3'),
    ('GPL-3 or any later version', 'GPL-3 or later version'),
    ('AGPL-3', 'Affero GPL-3'),
    ('LGPL-3', 'LGPL Version 3'),
    ('Other OSI approved licence', 'Other OSI Approved License'),
    ('OEEL-1', 'Odoo Enterprise Edition License v1.0'),
    ('OPL-1', 'Odoo Proprietary License v1.0'),
    ('Other proprietary', 'Other Proprietary License'),
]


class ScmRepositoryBranchModule(models.Model):
    _name = 'scm.repository.branch.module'
    _description = 'Odoo Addons by branch'
    _order = 'name asc, latest_version desc'

    name = fields.Char(
        'Technical Name', readonly=True, required=True, index=True)

    branch_id = fields.Many2one(
        'scm.repository.branch', 'Branch', required=True, auto_join=True,
        readonly=True, ondelete='cascade')
    version_id = fields.Many2one(
        related='branch_id.version_id', readonly=True, store=True)
    create_date = fields.Datetime('Added on', readonly=True)

    latest_version = fields.Char(readonly=True)
    shortdesc = fields.Char('Module Name', readonly=True)
    summary = fields.Char(readonly=True)
    description = fields.Text(readonly=True)
    description_html = fields.Html(readonly=True)
    author = fields.Char(readonly=True)
    maintainer = fields.Char(readonly=True)
    contributors = fields.Text(readonly=True)
    website = fields.Char(readonly=True)
    license = fields.Selection(LICENSES, readonly=True)
    application = fields.Boolean(readonly=True)
    auto_install = fields.Boolean('Automatic Installation', readonly=True)
    icon_image = fields.Binary(string='Icon', attachment=True, readonly=True)
    icon_url = fields.Char(compute='_get_icon_url', store=True)

    _sql_constraints = [
        ('uniq_module', 'UNIQUE (name, branch_id)',
         'A module must be unique per branch!'),
    ]

    @api.one
    def name_get(self):
        return self.id, '%s (%s)' % (self.shortdesc, self.name)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        recs = self.search([
            '|', ('name', operator, name), ('shortdesc', operator, name),
        ] + (args or []), limit=limit)
        return recs.name_get()

    @api.multi
    @api.depends('icon_image')
    def _get_icon_url(self):
        attachments = {
            att.res_id: att.id for att in self.env['ir.attachment'].search([
                ('res_model', '=', self._name),
                ('res_field', '=', 'icon_image'),
                ('res_id', 'in', self.ids),
            ])}
        for record in self:
            record.icon_url = '/web/image/%s' % attachments.get(record.id, '')

    @api.multi
    def action_try_me(self):
        self.ensure_one()
        running_build = self.branch_id.running_build_id
        if not running_build:
            build_to_run = self.branch_id.runnable_build_id
            if not build_to_run:
                raise UserError(_("No build to run"))
            build_to_run.start_container_from_registry()
            running_build = build_to_run
        return running_build.open()
