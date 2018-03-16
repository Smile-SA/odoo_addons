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
                if isinstance(path, tuple) and self.store:
                    path, domain = path
                    domain = list(domain)
                ##################
                # process stored fields
                stored = set(field for field in fields if field.compute and field.store)
                fields = set(fields) - stored
                if path == 'id':
                    target = records
                    # Added by Smile #
                    if domain:
                        target = target.filtered_from_domain(domain)
                    ##################
                else:
                    # don't move this line to function top, see log
                    env = records.env(user=SUPERUSER_ID, context={'active_test': False})
                    target = env[model_name].search([(path, 'in', records.ids)] + domain)
                if target:
                    for field in stored:
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
        if isinstance(path, tuple) and self.store:
            path, domain = path
        ##################
        target = env[field.model_name]
        computed = target.browse(env.computed[field])
        if path == 'id' and field.model_name == records._name:
            target = records - computed
        elif path and env.in_onchange:
            target = (target.browse(env.cache[field]) - computed).filtered(
                lambda rec: rec if path == 'id' else rec._mapped_cache(path) & records
            )
        else:
            target = target.browse(env.cache[field]) - computed
        # Added by Smile #
        if domain:
            target = target.filtered_from_domain(domain)
        ##################
        if target:
            spec.append((field, target._ids))
    return spec


def _add_trigger(self, env, path_str, field=None):
    # Added by Smile #
    domain = []
    if isinstance(path_str, tuple) and self.store:
        path_str, domain = path_str
    ##################
    path = path_str.split('.')
    # traverse path and add triggers on fields along the way
    for i, name in enumerate(path):
        model = env[field.comodel_name if field else self.model_name]
        field = model._fields[name]
        # env[self.model_name] --- path[:i] --> model with field

        if field is self:
            self.recursive = True
            continue

        # Added by Smile #
        trigger = '.'.join(path[:i] or ['id'])
        if domain:
            trigger = (trigger, tuple(domain))
        ##################
        # add trigger on field and its inverses to recompute self
        model._field_triggers.add(field, (self, trigger))

        # Added by Smile #
        trigger = '.'.join(path[:i + 1])
        if domain:
            trigger = (trigger, tuple(domain))
        ##################
        for invf in model._field_inverses[field]:
            invm = env[invf.model_name]
            invm._field_triggers.add(invf, (self, trigger))

Field.modified = modified
Field.modified_draft = modified_draft
Field._add_trigger = _add_trigger
