# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict
import time

from odoo import api, models
from odoo.exceptions import MissingError

from ..tools import PerfLogger


@api.model
def recompute(self, fnames=None, records=None):
    """ Recompute all function fields (or the given ``fnames`` if present).
        The fields and records to recompute have been determined by method
        :meth:`modified`.
    """
    logger = PerfLogger()

    if fnames is None:
        # recompute everything
        for field in list(self.env.fields_to_compute()):
            recs = self.env.records_to_compute(field)
            start = time.time()
            try:
                _recompute(self, field, recs)
            finally:
                duration = time.time() - start
                if duration >= logger.recompute_min_duration > 0:
                    logger.log_field_recomputation(
                        field.model_name, field.name, len(recs), duration)
    else:
        fields = [self._fields[fname] for fname in fnames]

        # check whether any 'records' must be computed
        if records is not None and not any(
                records & self.env.records_to_compute(field)
                for field in fields
        ):
            return

        # recompute the given fields on self's model
        for field in fields:
            recs = self.env.records_to_compute(field)
            start = time.time()
            try:
                _recompute(self, field, recs)
            finally:
                duration = time.time() - start
                if duration >= logger.recompute_min_duration > 0:
                    logger.log_field_recomputation(
                        field.model_name, field.name, len(recs), duration)


def _recompute(self, field, recs):
    if not recs:
        return
    if field.compute and field.store:
        # do not force recomputation on new records; those will be
        # recomputed by accessing the field on the records
        recs = recs.filtered('id')
        try:
            recs.mapped(field.name)
        except MissingError:
            existing = recs.exists()
            existing.mapped(field.name)
            # mark the field as computed on missing records, otherwise
            # they remain forever in the todo list, and lead to an
            # infinite loop...
            for f in recs.pool.field_computed[field]:
                self.env.remove_to_compute(f, recs - existing)
    else:
        self.env.cache.invalidate([(field, recs._ids)])
        self.env.remove_to_compute(field, recs)



models.BaseModel.recompute = recompute
