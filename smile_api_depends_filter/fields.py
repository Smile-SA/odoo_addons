# -*- coding: utf-8 -*-

from collections import defaultdict
import logging

from openerp import SUPERUSER_ID
from openerp.fields import Field

_logger = logging.getLogger(__name__)


def modified(self, records):
    """ Notify that field ``self`` has been modified on ``records``: prepare the
        fields/records to recompute, and return a spec indicating what to
        invalidate.
    """
    # invalidate the fields that depend on self, and prepare recomputation
    spec = [(self, records._ids)]

    # group triggers by model and path to reduce the number of calls to search()
    bymodel = defaultdict(lambda: defaultdict(list))
    for field, path in records._field_triggers[self]:
        bymodel[field.model_name][path].append(field)

    for model_name, bypath in bymodel.iteritems():
        for path, fields in bypath.iteritems():
            if path and any(field.compute and field.store for field in fields):
                # Added by Smile #
                domain = []
                if isinstance(path, tuple):
                    path, domain = path
                    domain = list(domain)
                ##################
                # process stored fields
                stored = set(field for field in fields if field.compute and field.store)
                fields = set(fields) - stored
                if path == 'id':
                    target0 = records
                    # Added by Smile #
                    if domain:
                        target0 = target0.filtered_from_domain(domain)
                    ##################
                else:
                    # don't move this line to function top, see log
                    env = records.env(user=SUPERUSER_ID, context={'active_test': False})
                    target0 = env[model_name].search([(path, 'in', records.ids)] + list(domain))
                if target0:
                    for field in stored:
                        # discard records to not recompute for field
                        target = target0 - records.env.protected(field)
                        if not target:
                            continue
                        spec.append((field, target._ids))
                        # recompute field on target in the environment of
                        # records, and as user admin if required
                        if field.compute_sudo:
                            target = target.with_env(records.env(user=SUPERUSER_ID))
                        else:
                            target = target.with_env(records.env)
                        target._recompute_todo(field)
            # process non-stored fields
            for field in fields:
                spec.append((field, None))

    return spec


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
            target = (target.browse(env.cache[field]) - protected).filtered(
                lambda rec: rec if path == 'id' else rec._mapped_cache(path) & records
            )
        else:
            target = target.browse(env.cache[field]) - protected
        # Added by Smile #
        if domain:
            target = target.filtered_from_domain(domain)
        ##################
        if target:
            spec.append((field, target._ids))
    return spec


def resolve_deps(self, model):
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
            _logger.warning("Field %s depends on itself; please fix its decorator @api.depends().", self)
        model, path = model0, dotnames.split('.')
        for i, fname in enumerate(path):
            field = model._fields[fname]
            # Changed by Smile #
            if domain and model == model0:
                result.append((model, field, (path[:i], tuple(domain))))
            else:
                result.append((model, field, path[:i]))
            ##################
            model = model0.env.get(field.comodel_name)

    # add self's model dependencies
    for mname, fnames in model0._depends.iteritems():
        model = model0.env[mname]
        for fname in fnames:
            field = model._fields[fname]
            result.append((model, field, None))

    # add indirect dependencies from the dependencies found above
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

    return result


def setup_triggers(self, model):
    """ Add the necessary triggers to invalidate/recompute ``self``. """
    for model, field, path in self.resolve_deps(model):
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

Field.modified = modified
Field.modified_draft = modified_draft
Field.resolve_deps = resolve_deps
Field.setup_triggers = setup_triggers
