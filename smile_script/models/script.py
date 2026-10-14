# -*- coding: utf-8 -*-
# (C) 2025 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from io import StringIO

from odoo import fields, models, tools, _
from odoo.exceptions import UserError
from odoo.sql_db import db_connect
from odoo.tools.convert import convert_xml_import

from odoo.addons.smile_log.tools import SmileDBLogger

_logger = logging.getLogger(__name__)


def _get_exception_message(exception):
    msg = exception
    if isinstance(exception, UserError):
        msg = exception.args[0]
    return str(msg)


class SmileScript(models.Model):
    _name = "smile.script"
    _description = "Maintenance Script"

    create_date = fields.Datetime("Created on",
                                  readonly=True)
    create_uid = fields.Many2one("res.users", "Created by",
                                 readonly=True)
    validation_date = fields.Datetime("Validated on",
                                      readonly=True)
    validation_user_id = fields.Many2one("res.users",
                                         "Validated by",
                                         readonly=True)
    name = fields.Char(required=True)
    description = fields.Text()
    type = fields.Selection(
        [
            ("python", "Python"),
            ("sql", "SQL"),
            ("xml", "XML"),
        ],
        "Type",
        required=True,
    )
    code = fields.Text(required=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("validated", "Validated"),
        ],
        required=True,
        default="draft",
        copy=False,
    )
    intervention_ids = fields.One2many(
        "smile.script.intervention",
        "script_id",
        "Interventions",
        readonly=True,
        copy=False,
    )
    expect_result = fields.Boolean("Expect a result")

    @staticmethod
    def _can_write_after_validation(vals):
        keys = vals and vals.keys() or []
        for field in keys:
            if field not in ["name"]:
                return False
        return True

    def write(self, vals):
        if not vals:
            return True
        if "validated" in self.mapped(
                "state"
        ) and not SmileScript._can_write_after_validation(vals):
            raise UserError(_("You can only modify draft scripts!"))
        return super().write(vals)

    def unlink(self):
        if "validated" in self.mapped("state"):
            raise UserError(_("You can only delete draft scripts!"))
        return super().unlink()

    def validate(self):
        if "validated" in self.mapped("state"):
            raise UserError(_("You can only validate draft scripts!"))
        return self.write(
            {
                "state": "validated",
                "validation_user_id": self.env.uid,
                "validation_date": fields.Datetime.now(),
            }
        )

    def _run(self, logger):
        self.ensure_one()
        if self.type == "sql":
            return self._run_sql()
        elif self.type == "xml":
            return self._run_xml()
        elif self.type == "python":
            return self._run_python(logger)
        raise NotImplementedError(self.type)

    def run(self):
        self.ensure_one()

        Intervention = self.env["smile.script.intervention"]
        if not self.env.context.get("test_mode") and self.state == "draft":
            raise UserError(_("You can only run validated scripts!"))
        intervention = Intervention.create(
            {
                "script_id": self.id,
                "test_mode": self.env.context.get("test_mode"),
            }
        )

        logger = SmileDBLogger(
            self.env.cr.dbname,
            "smile.script.intervention",
            intervention.id,
            self.env.uid
        )
        if not self.env.context.get("do_not_use_new_cursor"):
            intervention_cr = db_connect(self.env.cr.dbname).cursor()
        else:
            intervention_cr = self.env.cr
        intervention_vals = {}
        try:
            logger.info("Running script: %s\nCode:\n%s" % (self.name,
                                                           self.code))
            result = self.with_env(self.env(cr=intervention_cr))._run(logger)
            if not self.env.context.get("do_not_use_new_cursor"):
                if self.env.context.get("test_mode"):
                    logger.info("TEST MODE: Script rollbacking")
                    intervention_cr.rollback()
                else:
                    intervention_cr.commit()
            intervention_vals.update({"state": "done", "result": result})
            logger.info("Script execution SUCCEEDED: %s\n" % (self.name,))
        except Exception as e:
            intervention_vals.update(
                {
                    "state": "exception",
                    "result": _get_exception_message(e),
                }
            )
            logger.error(
                "Script execution FAILED: %s\nError:\n%s"
                % (self.name, _get_exception_message(e))
            )
        finally:
            if not self.env.context.get("do_not_use_new_cursor"):
                intervention_cr.close()
        intervention_vals.update({"end_date": fields.Datetime.now()})
        return intervention.write(intervention_vals)

    def run_test(self):
        return self.with_context(test_mode=True).run()

    def _run_python(self, logger):
        self.ensure_one()
        localdict = self._get_eval_context()
        localdict["logger"] = logger
        exec(self.code, localdict)
        if "result" in localdict:
            return localdict["result"]
        return "No expected result"

    def _get_eval_context(self):
        return {
            "self": self,
            "fields": fields,
            "tools": tools,
        }

    def _run_sql(self):
        self.ensure_one()
        self.env.cr.execute(self.code)
        if self.expect_result:
            return str(self.env.cr.fetchall())
        return "No expected result"

    def _run_xml(self):
        self.ensure_one()

        # Patch StringIO object with missing name attribute
        # Name attribute is required by the odoo function convert_xml_import
        stringio = StringIO(self.code)
        stringio.name = self.name

        try:
            # Use self.env instead of self.env.cr
            _logger.info("Starting XML import")
            convert_xml_import(self.env, __package__, stringio)
            _logger.info("XML import completed successfully")
        except Exception as e:
            _logger.error(f"Error during XML import: {str(e)}")
            raise

        return "No expected result"
