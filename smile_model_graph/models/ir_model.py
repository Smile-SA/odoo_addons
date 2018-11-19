# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import logging
from odoo import api, models
_logger = logging.getLogger(__name__)

try:
    import pydot
except ImportError:
    _logger.error('Please install pydot package for the good use of module'
                  ' `smile_model_graph`.')


class IrModel(models.Model):
    _inherit = 'ir.model'

    @staticmethod
    def add_graph_node(graph, nodes, name, label=None, color='black'):
        if name not in nodes:
            node = pydot.Node(label or name, color=color)
            nodes[name] = node
            graph.add_node(node)

    @staticmethod
    def add_graph_edge(graph, nodes, edges, src, dest, ttype,
                       direction='normal', reverse=False, label=''):
        key = (dest, src, ttype) if reverse else (src, dest, ttype)
        if key not in edges:
            edge = pydot.Edge(nodes[key[0]], nodes[key[1]], dir=direction,
                              label=label)
            edges[key] = edge
            graph.add_edge(edge)
        elif label != ' ':
            edges[key].set_label('%s, %s' % (edges[key].get_label(), label))

    @staticmethod
    def print_graph(graph, path):
        if path:
            return graph.write_png(path)
        return base64.encodestring(graph.create_png())

    @api.multi
    def _get_graph(self, show_relation_name=False):
        graph = pydot.Dot(graph_type='digraph')
        nodes, edges = {}, {}
        # Add nodes
        for model in self:
            color = 'red' if model.id in self._context.\
                get('selected_models', []) else 'black'
            IrModel.add_graph_node(graph, nodes, model.model, color=color)
        # Add edges
        for model in self:
            for field in model.field_id:
                if field.ttype in ('many2one', 'many2many', 'one2many') \
                        and field.relation in nodes:
                    vals = {
                        'ttype': 'm' if field.ttype == 'many2many' else 'o',
                        'direction': "both" if field.ttype == 'many2many'
                        else "normal",
                        'reverse': field.ttype == 'one2many',
                        'label': field.name if show_relation_name else ' ',
                    }
                    IrModel.add_graph_edge(graph, nodes, edges, model.model,
                                           field.relation, **vals)
        return graph

    @api.multi
    def _get_related_models(self, deep=1, excluded_model_names=None):
        new_model_names = []
        excluded_model_names = excluded_model_names or [m.model for m in self]
        if deep:  # allows an infinite deep if initial value is negative
            for model in self:
                for field in model.field_id:
                    if field.ttype in ('many2one', 'many2many', 'one2many') \
                        and (not excluded_model_names or
                             field.relation not in excluded_model_names):
                        new_model_names.append(field.relation)
        if new_model_names:
            excluded_model_names.extend(new_model_names)
            new_models = self.search([('model', 'in', new_model_names)])
            return self | new_models._get_related_models(deep - 1,
                                                         excluded_model_names)
        return self

    @api.multi
    def get_graph(self, deep=1, show_relation_name=False,
                  path='model_graph.png'):
        graph = self.with_context(selected_models=self.ids).\
            _get_related_models(deep)._get_graph(show_relation_name)
        return IrModel.print_graph(graph, path)
