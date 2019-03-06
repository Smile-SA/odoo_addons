# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import api, models, SUPERUSER_ID


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.multi
    def modified(self, fnames):
        """ Notify that fields have been modified on ``self``. This invalidates
            the cache, and prepares the recomputation of stored function fields
            (new-style fields only).

            :param fnames: iterable of field names that have been modified on
                records ``self``
        """
        # group triggers by (model, path) to minimize the calls to search()
        invalids = []
        triggers = defaultdict(set)
        for fname in fnames:
            mfield = self._fields[fname]
            # invalidate mfield on self, and its inverses fields
            invalids.append((mfield, self._ids))
            for field in self._field_inverses[mfield]:
                invalids.append((field, None))
            # group triggers by model and path to reduce the number of search()
            for field, path in self._field_triggers[mfield]:
                triggers[(field.model_name, path)].add(field)
        # process triggers, mark fields to be invalidated/recomputed
        for model_path, fields in triggers.items():
            model_name, path = model_path
            stored = {
                field for field in fields
                if field.compute and field.store}
            # process stored fields
            if path and stored:
                # Added by Smile #
                domain = []
                if isinstance(path, tuple):
                    path, domain = path
                    domain = list(domain)
                ##################
                # determine records of model_name linked by path to self
                if path == 'id':
                    # Modified by Smile #
                    target0 = self.filtered_from_domain(domain)
                #####################
                else:
                    Model = self.env[model_name]
                    f = Model._fields.get(path)
                    if f and f.store and f.type \
                            not in ('one2many', 'many2many'):
                        # path is direct (not dotted), stored,
                        # and inline -> optimise to raw sql
                        self.env.cr.execute('SELECT id FROM "%s" WHERE "%s" '
                                            'in %%s' % (Model._table, path),
                                            [tuple(self.ids)])
                        target0 = Model.browse(i for [i]
                                               in self.env.cr.fetchall())
                    else:
                        env = self.env(user=SUPERUSER_ID,
                                       context={'active_test': False})
                        # Modified by Smile #
                        target0 = env[model_name].search(
                            [(path, 'in', self.ids)] + list(domain))
                        #####################
                        target0 = target0.with_env(self.env)
                # prepare recomputation for each field on linked records
                for field in stored:
                    # discard records to not recompute for field
                    target = target0 - self.env.protected(field)
                    if not target:
                        continue
                    invalids.append((field, target._ids))
                    # mark field to be recomputed on target
                    if field.compute_sudo:
                        target = target.sudo()
                    target._recompute_todo(field)
            # process non-stored fields
            for field in (fields - stored):
                invalids.append((field, None))

        self.env.cache.invalidate(invalids)
