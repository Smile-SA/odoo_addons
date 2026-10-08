# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import logging
import random
import time
from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class PurgeData(models.Model):
    _name = "purge.data"
    _description = "Purge Data"

    name = fields.Char(string="Name")
    active = fields.Boolean(string="Active", default=True)
    model_id = fields.Many2one(
        "ir.model", string="Model", required=True, ondelete="cascade"
    )
    res_model_name = fields.Char(
        string="Model Name", related="model_id.model", readonly=True
    )
    use_date_range = fields.Boolean(string="Use Date Range", default=True)
    date_range = fields.Integer(string="Date Range")
    date_range_type = fields.Selection(
        [("days", "Days"), ("months", "Months"), ("years", "Years")],
        string="Date Range Type",
    )
    # proposed fields are fields related to the model_id and date type
    field_id = fields.Many2one(
        "ir.model.fields",
        string="Field",
        domain="[('model_id', '=', model_id), "
               "('ttype', 'in', ['date', 'datetime'])]",
    )
    batch_size = fields.Integer(string="Batch Size", default=1000)
    state = fields.Selection(
        [("draft", "Draft"), ("in_progress", "In progress")],
        string="State",
        default="draft",
    )
    deleted_records = fields.Integer(
        string="Deleted Records", readonly=True, default=0)
    # TODO : choose between domain or date range rule
    use_domain = fields.Boolean(string="Use Domain", default=False)
    domain = fields.Char(string="Domain")

    def action_purge_all(self):
        res_ids = self.search([("active", "=", True)])
        for res_id in res_ids:
            res_id.action_purge_records()

    def _purge_by_domain(self):
        raise NotImplementedError("This method is not implemented yet")

    def _purge_data(self, domain):
        purge_obj = self.env[self.model_id.model]
        last_rec_ids = purge_obj.browse()
        expect_deleted, reject_ids = purge_obj.browse(), purge_obj.browse()

        t1 = time.time()
        res = purge_obj._search(domain)
        all_records = set(purge_obj.browse(res).ids)
        _logger.info(
            "%s ids fetched in %s sec by ORM",
            len(all_records), time.time() - t1
        )

        while len(expect_deleted) < self.batch_size:
            _logger.info(
                "Purge data : %s records deleted, %s records rejected",
                len(expect_deleted),
                len(reject_ids),
            )
            # Randomly select records from all_records with
            # limit=self.batch_size
            # By doing this we avoid seeing the same records at each execution
            records_to_check = set(
                random.sample(
                    list(all_records), min(len(all_records), self.batch_size)
                )
            )
            record_ids = purge_obj.browse(records_to_check)
            if not record_ids:
                _logger.warning("Purge data : no more records to delete")
                break
            all_records -= records_to_check
            if last_rec_ids.sorted("id") == record_ids.sorted("id"):
                _logger.warning("Purge data : no more records to delete")
                break
            last_rec_ids = record_ids
            try:
                with self.env.cr.savepoint():
                    record_ids.unlink()
                expect_deleted |= record_ids
            except Exception:  # UserError, IntegrityError, AccessError...
                # fall back one by one to isolate the blocked records
                for record in record_ids:
                    try:
                        with self.env.cr.savepoint():
                            record.unlink()
                        expect_deleted |= record
                    except Exception:
                        _logger.info(
                            "Purge data : %s %s cannot be deleted",
                            record._name, record.id, exc_info=True,
                        )
                        reject_ids |= record

        _logger.info(
            "Purge data : done job for %s in %s sec. %s records deleted.",
            self.model_id.model,
            time.time() - t1,
            len(expect_deleted),
        )
        self.write(
            {
                "deleted_records": len(expect_deleted) + self.deleted_records,
                "state": "in_progress",
            }
        )

    def _purge_by_date_range(self):
        self.ensure_one()

        if self.model_id and self.field_id:
            if (
                self.date_range_type not in ("days", "months", "years")
                or self.date_range <= 0
            ):
                raise UserError(
                    _("Please set a positive date range and its type.")
                )
            domain = [
                (
                    self.field_id.name,
                    "<",
                    fields.Datetime.now()
                    - relativedelta(**{self.date_range_type: self.date_range}),
                )
            ]
            self._purge_data(domain)

    def action_purge_records(self):
        """
        This method is used to purge the data from the selected model.
        Search all the records from the selected model corresponding to the
        date range and delete them.
        """
        for rec in self:
            if not rec.active:
                continue
            if rec.use_domain:
                rec._purge_by_domain()
            elif rec.use_date_range:
                rec._purge_by_date_range()
            else:
                raise NotImplementedError("This method is not implemented yet")
