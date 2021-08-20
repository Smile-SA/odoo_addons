# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.smile_ci.models.scm_repository_branch_build import _logger


class ScmRepositoryBranch(models.Model):
    _inherit = 'scm.repository.branch'

    module_ids = fields.One2many(
        'scm.repository.branch.module', 'branch_id', 'Modules', readonly=True)
    modules_count = fields.Integer(compute='_count_modules')

    @api.one
    @api.depends('module_ids')
    def _count_modules(self):
        self.modules_count = len(self.module_ids)

    @api.one
    def _update_modules_list(self, modules_list):
        self._update_modules_vals(modules_list)
        _logger.info('Updating installed modules list for %s...'
                     % self.display_name)
        new_modules = {m['name']: m for m in modules_list}
        for old_module in self.module_ids:
            if old_module.name not in new_modules:
                # Remove module not installed anymore in last build
                old_module.unlink()
            else:
                # Update module installed yet in last build
                vals = new_modules[old_module.name]
                for field in vals:
                    if isinstance(vals[field], models.Model):
                        v_field = vals[field].id
                    else:
                        v_field = vals[field]
                    if isinstance(old_module[field], models.Model):
                        o_field = old_module[field].id
                    else:
                        o_field = old_module[field]
                    if v_field != o_field:
                        old_module.write(vals)
                        break
        # Create new modules
        old_modules = self.module_ids.mapped('name')
        for new_module, vals in new_modules.items():
            if new_module not in old_modules:
                self.module_ids.create(vals)

    @api.multi
    def _update_modules_vals(self, vals_list):
        self.ensure_one()
        for vals in vals_list:
            for field in models.MAGIC_COLUMNS:
                if field in vals:
                    del vals[field]
            vals['branch_id'] = self.id
            if not vals.get('license'):
                vals['license'] = self.version_id.default_license
            if vals.get('description_html'):
                del vals['description']
