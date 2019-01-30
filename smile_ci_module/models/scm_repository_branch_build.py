# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from distutils.version import LooseVersion
from functools import partial

from odoo import api, models

from odoo.addons.smile_docker.tools import get_exception_message
from odoo.addons.smile_ci.models.scm_repository_branch_build \
    import DBNAME, _logger


class ScmRepositoryBranchBuild(models.Model):
    _inherit = 'scm.repository.branch.build'

    @api.one
    def _set_build_result(self):
        super(ScmRepositoryBranchBuild, self)._set_build_result()
        if self.result.endswith('stable'):
            try:
                modules_list = self._get_modules_list()
                self.branch_id.sudo()._update_modules_list(modules_list)
            except Exception as e:
                _logger.error(
                    'Error while updating installed modules list for %s: %s'
                    % (self.branch_id.display_name, get_exception_message(e)))

    @api.multi
    def _get_modules_list(self):
        self.ensure_one()
        _logger.info('Getting modules installed in %s...'
                     % self.docker_container)
        fields_list = list(self.env['scm.repository.branch.module']._fields)
        for field in models.LOG_ACCESS_COLUMNS:
            if field in fields_list:
                fields_list.remove(field)
        sock_exec = partial(self._connect('object').execute,
                            DBNAME, self.branch_id.user_uid,
                            self.branch_id.user_passwd)
        if LooseVersion(self.branch_id.version_id.name) >= LooseVersion('8.0'):
            modules_list = sock_exec('ir.module.module', 'search_read',
                                     [('state', '=', 'installed')],
                                     fields_list)
        else:
            module_ids = sock_exec('ir.module.module', 'search',
                                   [('state', '=', 'installed')])
            modules_list = sock_exec('ir.module.module',
                                     'read', module_ids, fields_list)
        return modules_list
