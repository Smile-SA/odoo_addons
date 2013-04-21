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


class IrModel(Model):
    _inherit = 'ir.model'

    @staticmethod
    def add_graph_node(graph, nodes, name, label=None):
        if name not in nodes:
            node = pydot.Node(label or name)
            nodes[name] = node
            graph.add_node(node)

    @staticmethod
    def add_graph_edge(graph, nodes, edges, src, dest, ttype, direction='normal', reverse=False, label=''):
        key = (dest, src, ttype) if reverse else (src, dest, ttype)
        if key not in edges:
            edge = pydot.Edge(nodes[key[0]], nodes[key[1]], dir=direction, label=label)
            edges[key] = edge
            graph.add_edge(edge)
        elif label:
            edges[key].set_label('%s, %s' % (edges[key].get_label(), label))

    @staticmethod
    def print_graph(graph, path):
        if path:
            return graph.write_png(path)
        return base64.encodestring(graph.create_png())

    @staticmethod
    def _get_graph(models, show_relation_name=False):
        graph = pydot.Dot(graph_type='digraph')
        nodes, edges = {}, {}
        # Add nodes
        for model in models:
            IrModel.add_graph_node(graph, nodes, model.model)
        # Add edges
        for model in models:
            for field in model.field_id:
                if field.ttype in ('many2one', 'many2many', 'one2many') \
                        and field.relation in nodes:
                    vals = {
                        'ttype': 'm' if field.ttype == 'many2many' else 'o',
                        'direction': "both" if field.ttype == 'many2many' else "normal",
                        'reverse': field.ttype == 'one2many',
                        'label': field.name if show_relation_name else '',
                    }
                    IrModel.add_graph_edge(graph, nodes, edges, model.model, field.relation, **vals)
        return graph

    def _get_linked_models(self, cr, uid, models, deep=1, context=None):
        new_model_names = []
        if deep:  # allows an infinite deep if initial value is negative
            for model in models:
                for field in model.field_id:
                    if field.ttype in ('many2one', 'many2many', 'one2many'):
                        new_model_names.append(field.relation)
        if new_model_names:
            ids = self.search(cr, uid, [('model', 'in', new_model_names)], context=context)
            new_models = list(set(self.browse(cr, uid, ids, context)) - set(models))
            models.extend(self._get_linked_models(cr, uid, new_models, deep - 1, context))
        return list(set(models))

    def get_graph(self, cr, uid, ids, deep=1, show_relation_name=False, path='model_graph.png', context=None):
        models = self._get_linked_models(cr, uid, self.browse(cr, uid, ids, context), deep, context)
        graph = IrModel._get_graph(models, show_relation_name)
        return IrModel.print_graph(graph, path)
