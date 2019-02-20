# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import pydot

from odoo import api, fields, models


class Module(models.Model):
    _inherit = 'scm.repository.branch.module'

    dependencies = fields.Text(readonly=True)
    dependency_ids = fields.Many2many(
        'scm.repository.branch.module', string='Dependencies',
        compute='_get_dependencies')

    @api.one
    @api.depends('dependencies', 'branch_id.module_ids')
    def _get_dependencies(self):
        if self.dependencies:
            self.dependency_ids = self.branch_id.module_ids.filtered(
                lambda module: module.name in self.dependencies.split(','))

    @api.model
    def print_modules_graph(self, modules_list):
        graph = self._generate_graph(modules_list)
        return base64.b64encode(graph.create_png())

    @api.model
    def _generate_graph(self, modules_list):
        graph = pydot.Dot(graph_type='digraph')
        # Add nodes
        for module in modules_list:
            label = '%s (%s)' % (module['shortdesc'], module['name'])
            color = self._get_color(module)
            graph.add_node(pydot.Node(
                name=module['name'], label=label, color=color))
        # Add edges
        for module in modules_list:
            for dependency in module['dependencies'].split(','):
                if dependency:
                    graph.add_edge(pydot.Edge(
                        src=module['name'], dst=dependency))
        return graph

    @api.model
    def _get_color(self, module):
        color = 'black'
        if module['auto_install']:
            color = 'blue'
        if module['application']:
            color = 'green'
        return color
