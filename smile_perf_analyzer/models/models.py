# -*- coding: utf-8 -*-

from collections import defaultdict
import time

from odoo import api, models
from odoo.tools import frozendict

from ..tools import PerfLogger


@api.model
def recompute(self):
    """ Recompute stored function fields. The fields and records to
        recompute have been determined by method :meth:`modified`.
    """
    logger = PerfLogger()
    while self.env.has_todo():
        field, recs = self.env.get_todo()
        start = time.time()
        try:
            _recompute(self, field, recs)
        finally:
            duration = time.time() - start
            if duration >= logger.recompute_min_duration > 0:
                logger.log_field_recomputation(field.model_name, field.name, len(recs), duration)


def _recompute(self, field, recs):
    # determine the fields to recompute
    fs = self.env[field.model_name]._field_computed[field]
    ns = [f.name for f in fs if f.store]
    # evaluate fields, and group record ids by update
    updates = defaultdict(set)
    for rec in recs.exists():
        vals = rec._convert_to_write({n: rec[n] for n in ns})
        updates[frozendict(vals)].add(rec.id)
    # update records in batch when possible
    with recs.env.norecompute():
        for vals, ids in updates.iteritems():
            recs.browse(ids)._write(dict(vals))
    # mark computed fields as done
    map(recs._recompute_done, fs)


models.BaseModel.recompute = recompute
