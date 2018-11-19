# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict
import time

from odoo import api, models
from odoo.exceptions import MissingError
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
                logger.log_field_recomputation(
                    field.model_name, field.name, len(recs), duration)


def _recompute(self, field, recs):
    # determine the fields to recompute
    fs = self.env[field.model_name]._field_computed[field]
    ns = [f.name for f in fs if f.store]
    # evaluate fields, and group record ids by update
    updates = defaultdict(set)
    for rec in recs:
        try:
            vals = {n: rec[n] for n in ns}
        except MissingError:
            continue
        vals = rec._convert_to_write(vals)
        updates[frozendict(vals)].add(rec.id)
    # update records in batch when possible
    with recs.env.norecompute():
        for vals, ids in updates.items():
            target = recs.browse(ids)
            try:
                target._write(dict(vals))
            except MissingError:
                # retry without missing records
                target.exists()._write(dict(vals))
    # mark computed fields as done
    for f in fs:
        recs._recompute_done(f)


models.BaseModel.recompute = recompute
