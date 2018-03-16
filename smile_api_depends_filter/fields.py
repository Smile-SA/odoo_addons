# -*- coding: utf-8 -*-

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
    for field, path in self._triggers:
        if path and field.compute and field.store:
            # don't move this line to function top, see log
            env = records.env(user=SUPERUSER_ID, context={'active_test': False})
            # Added by Smile #
            domain = []
            if isinstance(path, tuple) and self.store:
                path, domain = path
            ##################
            target = env[field.model_name].search([(path, 'in', records.ids)] + domain)
            if target:
                spec.append((field, target._ids))
                # recompute field on target in the environment of records,
                # and as user admin if required
                if field.compute_sudo:
                    target = target.with_env(records.env(user=SUPERUSER_ID))
                else:
                    target = target.with_env(records.env)
                target._recompute_todo(field)
        else:
            spec.append((field, None))

    return spec


def modified_draft(self, records):
    """ Same as :meth:`modified`, but in draft mode. """
    env = records.env

    # invalidate the fields on the records in cache that depend on
    # ``records``, except fields currently being computed
    spec = []
    for field, path in self._triggers:
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
        if path == 'id':
            target = records - computed
        elif path:
            target = (target.browse(env.cache[field]) - computed).filtered(
                lambda rec: rec._mapped_cache(path) & records
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


def setup_triggers(self, env):
    """ Add the necessary triggers to invalidate/recompute ``self``. """
    model = env[self.model_name]
    for path in self.depends:
        # Added by Smile #
        domain = None
        if isinstance(path, tuple):
            path, domain = path
        ##################
        self._setup_dependency([], model, path.split('.'), domain)


def _setup_dependency(self, path0, model, path1, domain=None):
    """ Make ``self`` depend on ``model``; `path0 + path1` is a dependency of
        ``self``, and ``path0`` is the sequence of field names from ``self.model``
        to ``model``.
    """
    env = model.env
    head, tail = path1[0], path1[1:]

    if head == '*':
        # special case: add triggers on all fields of model (except self)
        fields = set(model._fields.itervalues()) - set([self])
    else:
        fields = [model._fields[head]]

    for field in fields:
        if field == self:
            _logger.debug("Field %s is recursively defined", self)
            self.recursive = True
            continue

        # Added by Smile #
        trigger = '.'.join(path0 or ['id'])
        if domain:
            trigger = (trigger, domain)
        ##################
        # _logger.debug("Add trigger on %s to recompute %s", field, self)
        field.add_trigger((self, trigger))

        # Added by Smile #
        trigger = '.'.join(path0 + [head])
        if domain:
            trigger = (trigger, domain)
        ##################
        # add trigger on inverse fields, too
        for invf in field.inverse_fields:
            # _logger.debug("Add trigger on %s to recompute %s", invf, self)
            invf.add_trigger((self, trigger))

        # recursively traverse the dependency
        if tail:
            comodel = env[field.comodel_name]
            self._setup_dependency(path0 + [head], comodel, tail, domain)

Field.modified = modified
Field.modified_draft = modified_draft
Field.setup_triggers = setup_triggers
Field._setup_dependency = _setup_dependency
