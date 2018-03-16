# -*- coding: utf-8 -*-

import time

from openerp import api, models
from openerp.exceptions import MissingError

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
    field, recs = self.env.get_todo()
    # evaluate the fields to recompute, and save them to database
    names = [
        f.name
        for f in field.computed_fields
        if f.store and self.env.field_todo(f)
    ]
    for rec in recs:
        try:
            values = rec._convert_to_write({
                name: rec[name] for name in names
            })
            with rec.env.norecompute():
                map(rec._recompute_done, field.computed_fields)
                rec._write(values)
        except MissingError:
            pass
    # mark the computed fields as done
    map(recs._recompute_done, field.computed_fields)

models.BaseModel.recompute = recompute
