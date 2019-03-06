# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo.fields import Field

_logger = logging.getLogger(__name__)


def modified_draft(self, records):
    """ Same as :meth:`modified`, but in draft mode. """
    env = records.env

    # invalidate the fields on the records in cache that depend on
    # ``records``, except fields currently being computed
    spec = []
    for field, path in records._field_triggers[self]:
        if not field.compute:
            # Note: do not invalidate non-computed fields. Such fields may
            # require invalidation in general (like *2many fields with
            # domains) but should not be invalidated in this case, because
            # we would simply lose their values during an onchange!
            continue
        # Added by Smile #
        domain = []
        if isinstance(path, tuple):
            path, domain = path
        ##################
        target = env[field.model_name]
        protected = env.protected(field)
        if path == 'id' and field.model_name == records._name:
            target = records - protected
        elif path and env.in_onchange:
            target = (env.cache.get_records(target, field) -
                      protected).filtered(
                lambda rec: rec if path == 'id'
                else rec._mapped_cache(path) & records
            )
        else:
            target = env.cache.get_records(target, field) - protected
        # Added by Smile #
        if domain:
            target = target.filtered_from_domain(domain)
        ##################
        if target:
            spec.append((field, target._ids))
    return spec


def resolve_deps(self, model, path0=[], seen=frozenset()):
    """ Return the dependencies of ``self`` as tuples ``(model, field, path)``,
        where ``path`` is an optional list of field names.
    """
    model0 = model
    result = []

    # add self's own dependencies
    for dotnames in self.depends:
        # Added by Smile #
        domain = []
        if isinstance(dotnames, tuple):
            dotnames, domain = dotnames
        ##################
        if dotnames == self.name:
            _logger.warning("Field %s depends on itself; please fix "
                            "its decorator @api.depends().", self)
        model, path = model0, path0

        for fname in dotnames.split('.'):
            field = model._fields[fname]
            # Changed by Smile #
            if domain and model == model0:
                result.append((model, field, (path, tuple(domain))))
            else:
                result.append((model, field, path))
            ##################
            model = model0.env.get(field.comodel_name)
            path = None if path is None else path + [fname]

    # add self's model dependencies
    for mname, fnames in model0._depends.items():
        model = model0.env[mname]
        for fname in fnames:
            field = model._fields[fname]
            result.append((model, field, None))

    # add indirect dependencies from the dependencies found above
    seen = seen.union([self])
    for model, field, path in list(result):
        for inv_field in model._field_inverses[field]:
            inv_model = model0.env[inv_field.model_name]
            # Changed by Smile #
            if path is None:
                inv_path = None
            elif isinstance(path, tuple):
                path, domain = path
                inv_path = (path + [field.name], tuple(domain))
            else:
                inv_path = path + [field.name]
            ##################
            result.append((inv_model, inv_field, inv_path))
        if not field.store and field not in seen:
            result += field.resolve_deps(model, path, seen)

    return result


def setup_triggers(self, model):
    """ Add the necessary triggers to invalidate/recompute ``self``. """
    for model, field, path in self.resolve_deps(model):
        if self.store and not field.store:
            _logger.info(
                "Field %s depends on non-stored field %s", self, field)
        if field is not self:
            # Changed by Smile #
            if path is None:
                path_str = None
            elif isinstance(path, tuple):
                path, domain = path
                path_str = ('.'.join(path) or 'id', domain)
            else:
                path_str = '.'.join(path) or 'id'
            ##################
            model._field_triggers.add(field, (self, path_str))
        elif path:
            self.recursive = True
            # Changed by Smile #
            if isinstance(path, tuple):
                path, domain = path
                path_str = ('.'.join(path), domain)
            else:
                path_str = '.'.join(path)
            ##################
            model._field_triggers.add(field, (self, path_str))


Field.modified_draft = modified_draft
Field.resolve_deps = resolve_deps
Field.setup_triggers = setup_triggers
