# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import base64
import pydot

from odoo import api, models, _


class IrModuleModule(models.Model):
    _inherit = "ir.module.module"

    @staticmethod
    def add_graph_node(graph, nodes, name, label=None, color='black'):
        if name not in nodes:
            node = pydot.Node(name, color=color)
            nodes[name] = node
            graph.add_node(node)

    @staticmethod
    def add_graph_edge(graph, nodes, edges, src, dest):
        key = (src, dest)
        if key not in edges:
            edges.append(key)
            graph.add_edge(pydot.Edge(*key))

    @staticmethod
    def print_graph(graph, path):
        if path:
            return graph.write_png(path)
        return base64.encodestring(graph.create_png())

    def _get_color(self):
        color = 'black'
        valid_states = ('installed', 'to upgrade', 'to remove')
        if self.state in ('uninstallable', 'unknown'):
            color = 'grey'
        elif self.state not in valid_states:
            color = 'red'
        elif self.auto_install and self.state in valid_states:
            color = 'blue'
        return color

    @api.multi
    def _add_graph_nodes_and_edges(self, graph):
        nodes = dict([(node.get_name(), node) for node in graph.get_nodes()])
        edges = [(edge.get_source(), edge.get_destination()) for edge in graph.get_edges()]
        module_names = [m.name for m in self]
        # Add nodes
        for module in self:
            color = module._get_color()
            IrModuleModule.add_graph_node(graph, nodes, module.name, color=color)
        # Add edges
        for module in self:
            for dependency in module.dependencies_id:
                if dependency.name in module_names:
                    IrModuleModule.add_graph_edge(graph, nodes, edges, module.name, dependency.name)

    @api.multi
    def _get_dependency_modules(self, stream='down', states=None):
        dependency_modules = None
        if stream == 'down':
            dependency_names = []
            for module in self:
                for dependency in module.dependencies_id:
                    dependency_names.append(dependency.name)
            if dependency_names:
                dependency_modules = self.search([('name', 'in', dependency_names)])
        elif stream == 'up':
            dependency_obj = self.env['ir.module.module.dependency']
            dependencies = dependency_obj.search([('name', 'in', [m.name for m in self])])
            dependency_modules = self.browse([d.module_id.id for d in dependencies])
        if states:
            return dependency_modules and dependency_modules.filtered(lambda a: a.state in states)
        return dependency_modules

    @api.multi
    def _get_graph_modules(self, stream='down', states=None):
        new_modules = self.browse(self.ids)  # Copy self
        while new_modules:
            new_modules = new_modules._get_dependency_modules(stream, states)
            if new_modules:
                self |= new_modules
        return self

    @api.multi
    def get_graph(self, stream='down', states=None, path='module_graph.png'):
        assert stream in ('down', 'up', 'up-down'), "stream must be in ('down', 'up', 'up-down')"
        graph = pydot.Dot(graph_type='digraph')
        for st in stream.split('-'):
            modules = self._get_graph_modules(st, states)
            modules._add_graph_nodes_and_edges(graph)
        return IrModuleModule.print_graph(graph, path)

    @api.multi
    def open_graph_wizard(self):
        return {
            'name': _('Modules Graph'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.module.module.graph_wizard',
            'view_mode': 'form',
            'context': {'active_ids': self.ids},
            'target': 'new',
        }
