# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.tools import OrderedSet
from odoo.models import regex_field_agg, VALID_AGGREGATE_FUNCTIONS
from odoo.exceptions import UserError


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def _read_group_raw(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        self.check_access_rights('read')
        query = self._where_calc(domain)
        fields = fields or [f.name for f in self._fields.values() if f.store]

        groupby = [groupby] if isinstance(groupby, str) else list(OrderedSet(groupby))
        groupby_list = groupby[:1] if lazy else groupby
        annotated_groupbys = [self._read_group_process_groupby(gb, query) for gb in groupby_list]
        groupby_fields = [g['field'] for g in annotated_groupbys]
        order = orderby or ','.join([g for g in groupby_list])
        groupby_dict = {gb['groupby']: gb for gb in annotated_groupbys}

        self._apply_ir_rules(query, 'read')
        for gb in groupby_fields:
            assert gb in self._fields, "Unknown field %r in 'groupby'" % gb
            gb_field = self._fields[gb].base_field
            assert gb_field.store and gb_field.column_type, \
                "Fields in 'groupby' must be regular database-persisted fields " \
                "(no function or related fields), or function fields with store=True"

        aggregated_fields = []
        select_terms = []
        fnames = []                     # list of fields to flush

        for fspec in fields:
            if fspec == 'sequence':
                continue
            if fspec == '__count':
                # the web client sometimes adds this pseudo-field in the list
                continue

            match = regex_field_agg.match(fspec)
            if not match:
                raise UserError(_("Invalid field specification %r.", fspec))

            name, func, fname = match.groups()
            if func:
                # we have either 'name:func' or 'name:func(fname)'
                fname = fname or name
                field = self._fields.get(fname)
                if not field:
                    raise ValueError("Invalid field %r on model %r" % (fname, self._name))
                if not (field.base_field.store and field.base_field.column_type):
                    raise UserError(_("Cannot aggregate field %r.", fname))
                if func not in VALID_AGGREGATE_FUNCTIONS:
                    raise UserError(_("Invalid aggregation function %r.", func))
            else:
                # we have 'name', retrieve the aggregator on the field
                field = self._fields.get(name)
                if not field:
                    raise ValueError("Invalid field %r on model %r" % (name, self._name))
                if not (field.base_field.store and
                        field.base_field.column_type and field.group_operator):
                    continue
                func, fname = field.group_operator, name
            # Added Smile
            find_field = self.env['ir.model.fields'].sudo().search([
                ('model', '=', self._name),
                ('name', '=', name),
            ], limit=1)
            if find_field and find_field.custom_group_operator:
                func = find_field.custom_group_operator
            # End Smile

            fnames.append(fname)

            if fname in groupby_fields:
                continue
            if name in aggregated_fields:
                raise UserError(_("Output name %r is used twice.", name))
            aggregated_fields.append(name)

            expr = self._inherits_join_calc(self._table, fname, query)
            if func.lower() == 'count_distinct':
                term = 'COUNT(DISTINCT %s) AS "%s"' % (expr, name)
            else:
                term = '%s(%s) AS "%s"' % (func, expr, name)
            select_terms.append(term)

        for gb in annotated_groupbys:
            select_terms.append('%s as "%s" ' % (gb['qualified_field'], gb['groupby']))

        self._flush_search(domain, fields=fnames + groupby_fields)

        groupby_terms, orderby_terms = self._read_group_prepare(order, aggregated_fields, annotated_groupbys, query)
        from_clause, where_clause, where_clause_params = query.get_sql()
        if lazy and (len(groupby_fields) >= 2 or not self._context.get('group_by_no_leaf')):
            count_field = groupby_fields[0] if len(groupby_fields) >= 1 else '_'
        else:
            count_field = '_'
        count_field += '_count'

        prefix_terms = lambda prefix, terms: (prefix + " " + ",".join(terms)) if terms else ''
        prefix_term = lambda prefix, term: ('%s %s' % (prefix, term)) if term else ''

        query = """
                SELECT min("%(table)s".id) AS id, count("%(table)s".id) AS "%(count_field)s" %(extra_fields)s
                FROM %(from)s
                %(where)s
                %(groupby)s
                %(orderby)s
                %(limit)s
                %(offset)s
            """ % {
            'table': self._table,
            'count_field': count_field,
            'extra_fields': prefix_terms(',', select_terms),
            'from': from_clause,
            'where': prefix_term('WHERE', where_clause),
            'groupby': prefix_terms('GROUP BY', groupby_terms),
            'orderby': prefix_terms('ORDER BY', orderby_terms),
            'limit': prefix_term('LIMIT', int(limit) if limit else None),
            'offset': prefix_term('OFFSET', int(offset) if limit else None),
        }
        self._cr.execute(query, where_clause_params)
        fetched_data = self._cr.dictfetchall()

        if not groupby_fields:
            return fetched_data

        self._read_group_resolve_many2one_fields(fetched_data, annotated_groupbys)

        data = [{k: self._read_group_prepare_data(k, v, groupby_dict) for k, v in r.items()} for r in fetched_data]

        if self.env.context.get('fill_temporal') and data:
            data = self._read_group_fill_temporal(data, groupby, aggregated_fields,
                                                  annotated_groupbys)

        result = [self._read_group_format_result(d, annotated_groupbys, groupby, domain) for d in data]

        if lazy:
            # Right now, read_group only fill results in lazy mode (by default).
            # If you need to have the empty groups in 'eager' mode, then the
            # method _read_group_fill_results need to be completely reimplemented
            # in a sane way
            result = self._read_group_fill_results(
                domain, groupby_fields[0], groupby[len(annotated_groupbys):],
                aggregated_fields, count_field, result, read_group_order=order,
            )
        return result
