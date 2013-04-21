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

from osv.orm import Model


class IrModuleModule(Model):
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

    @staticmethod
    def _get_color(module):
        color = 'black'
        if module.state in ('uninstallable', 'unknown'):
            color = 'grey'
        elif module.state not in ('installed', 'to_upgrade', 'to_remove'):
            color = 'red'
        return color

    @staticmethod
    def _add_graph_nodes_and_edges(graph, modules):
        nodes, edges = {}, []
        module_names = [m.name for m in modules]
        # Add nodes
        for module in modules:
            color = IrModuleModule._get_color(module)
            IrModuleModule.add_graph_node(graph, nodes, module.name, color=color)
        # Add edges
        for module in modules:
            for dependency in module.dependencies_id:
                if dependency.name in module_names:
                    IrModuleModule.add_graph_edge(graph, nodes, edges, module.name, dependency.name)

    def _get_dependency_modules(self, cr, uid, modules, stream='down', states=None, context=None):
        dependency_modules = []
        if stream == 'down':
            dependency_names = []
            for module in modules:
                for dependency in module.dependencies_id:
                    dependency_names.append(dependency.name)
            if dependency_names:
                ids = self.search(cr, uid, [('name', 'in', dependency_names)], context=context)
                dependency_modules = self.browse(cr, uid, ids, context)
        elif stream == 'up':
            dependency_obj = self.pool.get('ir.module.module.dependency')
            dependency_ids = dependency_obj.search(cr, uid, [('name', 'in', [m.name for m in modules])], context=context)
            dependency_modules = [d.module_id for d in dependency_obj.browse(cr, uid, dependency_ids, context)]
        if states:
            return filter(lambda a: a.state in states, dependency_modules)
        return dependency_modules

    def _get_graph_modules(self, cr, uid, ids, stream='down', states=None, context=None):
        modules = self.browse(cr, uid, ids, context)
        new_modules = modules[:]
        while new_modules:
            new_modules = self._get_dependency_modules(cr, uid, modules, stream, states, context)
            new_modules = list(set(new_modules) - set(modules))
            modules.extend(new_modules)
        return modules

    def get_graph(self, cr, uid, ids, stream='down', states=None, path='module_graph.png', context=None):
        assert stream in ('down', 'up', 'up-down'), "stream must be in ('down', 'up', 'up-down')"
        graph = pydot.Dot(graph_type='digraph')
        for st in stream.split('-'):
            modules = self._get_graph_modules(cr, uid, ids, st, states, context)
            IrModuleModule._add_graph_nodes_and_edges(graph, modules)
        return IrModuleModule.print_graph(graph, path)
