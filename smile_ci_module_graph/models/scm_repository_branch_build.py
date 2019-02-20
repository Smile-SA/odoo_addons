# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from distutils.version import LooseVersion
from functools import partial

from odoo import api, models

from odoo.addons.smile_ci.models.scm_repository_branch_build import DBNAME


class ScmRepositoryBranchBuild(models.Model):
    _inherit = 'scm.repository.branch.build'

    @api.multi
    def _get_modules_list(self):
        modules_list = super(ScmRepositoryBranchBuild, self). \
            _get_modules_list()
        self._update_modules_list_with_dependencies(modules_list)
        self._attach_modules_graph(modules_list)
        return modules_list

    @api.one
    def _update_modules_list_with_dependencies(self, modules_list):
        module_ids = [m['id'] for m in modules_list]
        sock_exec = partial(self._connect('object').execute,
                            DBNAME, self.branch_id.user_uid,
                            self.branch_id.user_passwd)
        if LooseVersion(self.branch_id.version_id.name) >= LooseVersion('8.0'):
            dependencies_list = sock_exec(
                'ir.module.module.dependency', 'search_read',
                [('module_id', 'in', module_ids)], ['name', 'module_id'])
        else:
            dependency_ids = sock_exec(
                'ir.module.module.dependency', 'search',
                [('module_id', 'in', module_ids)])
            dependencies_list = sock_exec(
                'ir.module.module.dependency', 'read',
                dependency_ids, ['name', 'module_id'])
        dependencies_by_module = {}
        for dependency in dependencies_list:
            dependencies_by_module.setdefault(
                dependency['module_id'][0], []).append(dependency['name'])
        for module in modules_list:
            module['dependencies'] = ','.join(
                dependencies_by_module.get(module['id'], []))

    @api.one
    def _attach_modules_graph(self, modules_list):
        content = self.env['scm.repository.branch.module']. \
            print_modules_graph(modules_list)
        filename = 'modules_graph.png'
        self.env['ir.attachment'].create({
            'name': filename,
            'datas_fname': filename,
            'datas': content,
            'res_model': self._name,
            'res_id': self.id,
        })
