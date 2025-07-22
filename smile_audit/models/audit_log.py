from dateutil import tz
import re
from odoo.osv import expression

from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval, datetime

import logging

_logger = logging.getLogger(__name__)


class AuditLog(models.Model):
    _name = "audit.log"
    _description = "Audit Log"
    _order = "create_date desc, id desc"

    name = fields.Char(
        "Resource Name", size=256, compute="_get_name", search="_search_name"
    )
    create_date = fields.Datetime("Date", readonly=True)
    user_id = fields.Many2one(
        "res.users", "User", required=True, readonly=True
    )
    model_id = fields.Many2one(
        "ir.model", "Model", required=True, readonly=True, ondelete="cascade"
    )
    model = fields.Char(
        related="model_id.model",
        string="Log Model",
        store=True,
        readonly=True,
        index=True,
    )
    res_id = fields.Integer("Resource Id", readonly=True)
    method = fields.Char("Method", size=64, readonly=True)
    data = fields.Text("Data", readonly=True)
    data_html = fields.Html("HTML Data", readonly=True, compute="_render_html")

    def _get_name(self):  # noqa: CCR001
        for rec in self:
            if rec.model_id and rec.res_id:
                record = (
                    rec.env[rec.model_id.model].browse(rec.res_id).exists()
                )
                if record:
                    rec.name = record.display_name
                else:
                    try:
                        data = safe_eval(
                            rec.data or "{}", {"datetime": datetime}
                        )
                        rec_name = rec.env[rec.model_id.model]._rec_name
                        if rec_name in data.get("new", {}):
                            rec.name = data["new"][rec_name]
                        elif rec_name in data.get("old", {}):
                            rec.name = data["old"][rec_name]
                        else:
                            rec.name = "id=%s" % rec.res_id
                    except Exception:
                        try:
                            data_str = rec.data.replace(
                                "defaultdict(<class 'list'>, {})", "{}"
                            )
                            data_str = re.sub(
                                r"Markup\('([^']*)'\)", r"'\1'", data_str
                            )

                            data = safe_eval(data_str, {"datetime": datetime})
                            rec_name = rec.env[rec.model_id.model]._rec_name
                            if rec_name in data.get("new", {}):
                                rec.name = data["new"][rec_name]
                            elif rec_name in data.get("old", {}):
                                rec.name = data["old"][rec_name]
                            else:
                                if "name" in data.get("new", {}):
                                    rec.name = data["new"]["name"]
                                elif "name" in data.get("old", {}):
                                    rec.name = data["old"]["name"]
                                else:
                                    rec.name = "id=%s" % rec.res_id
                        except Exception:
                            data_str = rec.data
                            if data_str and "'name': '" in data_str:
                                match = re.search(
                                    r"'name': '([^']*)'", data_str
                                )
                                if match:
                                    rec.name = match.group(1)
                                else:
                                    rec.name = "id=%s" % rec.res_id
                            else:
                                rec.name = "id=%s" % rec.res_id
            else:
                rec.name = ""

    def _search_name(self, operator, value):  # noqa: CCR001
        if operator not in (
            "=",
            "!=",
            "like",
            "ilike",
            "not like",
            "not ilike",
        ):
            raise UserError(_("Unsupported search operator for name field"))

        audited_models = self.env["audit.rule"].search([]).mapped("model_id")
        domain = []
        for model in audited_models:
            model_name = model.model
            if model_name in self.env:
                try:
                    model_obj = self.env[model_name]
                    records = model_obj.search(
                        [(model_obj._rec_name, operator, value)]
                    )
                    if records:
                        domain = expression.OR(
                            [
                                domain,
                                [
                                    "&",
                                    ("model_id", "=", model.id),
                                    ("res_id", "in", records.ids),
                                ],
                            ]
                        )
                except Exception as e:
                    _logger.debug(
                        f"Error searching in model {model_name}: {e}"
                    )
                    continue
        return domain or [("id", "=", False)]

    def _format_value(self, field, value):  # noqa: CCR001
        self.ensure_one()
        if not value and field.type not in ("boolean", "integer", "float"):
            return ""
        if field.type == "selection":
            selection = field.selection
            if callable(selection):
                selection = selection(self.env[self.model_id.model])
            return dict(selection).get(value, value)
        if field.type == "many2one" and value:
            if isinstance(value, int):
                return (
                    self.env[field.comodel_name]
                    .browse(value)
                    .exists()
                    .display_name
                    or value
                )
            else:
                return value
        if field.type == "reference" and value:
            res_model, res_id = value.split(",")
            return (
                self.env[res_model].browse(int(res_id)).exists().display_name
                or value
            )
        if field.type in ("one2many", "many2many") and value:
            return ", ".join(
                [
                    self.env[field.comodel_name]
                    .browse(rec_id)
                    .exists()
                    .display_name
                    or str(rec_id)
                    for rec_id in value
                    if isinstance(rec_id, int)
                ]
            )
        if field.type == "binary" and value:
            return "<binary data>"
        if field.type == "datetime":
            from_tz = tz.tzutc()
            to_tz = tz.gettz(self.env.user.tz)
            datetime_wo_tz = value
            datetime_with_tz = datetime_wo_tz.replace(tzinfo=from_tz)
            return fields.Datetime.to_string(
                datetime_with_tz.astimezone(to_tz)
            )
        return value

    def _get_content(self):  # noqa: CCR001
        self.ensure_one()
        content = []

        try:
            data = safe_eval(self.data or "{}", {"datetime": datetime})
        except Exception:
            data_str = self.data or "{}"
            data_str = data_str.replace(
                "defaultdict(<class 'list'>, {})", "{}"
            )
            data_str = re.sub(r"Markup\('([^']*)'\)", r"'\1'", data_str)

            try:
                data = safe_eval(data_str, {"datetime": datetime})
            except Exception:
                data = {"old": {}, "new": {}}

        if "old" not in data:
            data["old"] = {}
        if "new" not in data:
            data["new"] = {}

        RecordModel = self.env[self.model_id.model]
        for fname in set(data["new"].keys()) | set(data["old"].keys()):
            field = RecordModel._fields.get(fname)
            if field and (
                not field.groups or self.user_has_groups(groups=field.groups)
            ):
                old_value = self._format_value(
                    field, data["old"].get(fname, "")
                )
                new_value = self._format_value(
                    field, data["new"].get(fname, "")
                )
                if old_value != new_value:
                    label = field.get_description(self.env)["string"]
                    content.append((label, old_value, new_value))
        return content

    def _render_html(self):  # noqa: CCR001
        for rec in self:
            thead = ""
            for head in (_("Field"), _("Old value"), _("New value")):
                thead += "<th>%s</th>" % head
            thead = "<thead><tr>%s</tr></thead>" % thead

            tbody = ""
            for line in rec._get_content():
                row = ""
                for item in line:
                    if item is None:
                        item = ""
                    row += "<td>%s</td>" % str(item)
                tbody += "<tr>%s</tr>" % row

            tbody = "<tbody>%s</tbody>" % tbody
            rec.data_html = (
                '<table class="o_list_view table table-condensed '
                'table-striped">%s%s</table>' % (thead, tbody)
            )

    def unlink(self):
        raise UserError(_("You cannot remove audit logs!"))
