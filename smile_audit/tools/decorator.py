import sys

from odoo import api

if sys.version_info > (3,):
    long = int


def audit_decorator(method):  # noqa: CCR001
    def update_type_defaultdict(values):
        for key in values.keys():
            if str(type(values[key])) == "<class 'collections.defaultdict'>":
                values[key] = dict(values[key])
            elif type(values[key]) is dict:
                update_type_defaultdict(values[key])

    def get_new_values(self):
        new_values = []
        for record in self:
            vals = {}
            for fname in self._fields:
                vals[fname] = self._fields[fname].convert_to_read(
                    record[fname], record, use_display_name=True
                )
            new_values.append(vals)
        return new_values

    @api.model
    def audit_create(self, vals):
        result = audit_create.origin(self, vals)
        record = (
            self.browse(result) if isinstance(result, (int, long)) else result
        )
        rule = self._get_audit_rule("create")
        if rule:
            new_values = record.read(load="_classic_write")
            keys = new_values[0].keys()
            for key in keys:
                if (
                    str(type(new_values[0][key]))
                    == "<class 'markupsafe.Markup'>"
                ):
                    new_values[0][key] = str(new_values[0][key])
            update_type_defaultdict(new_values[0])
            rule.log("create", new_values=new_values)
        return result

    def audit_write(self, vals):  # noqa: CCR001
        rule = None
        if self._name != self._context.get("audit_rec_model") or (
            self._name == self._context.get("audit_rec_model")
            and self.ids != self._context.get("audit_rec_ids")
        ):
            rule = self._get_audit_rule("write")
        if rule:
            old_values = self.sudo().read(load="_classic_write")
        result = audit_write.origin(self, vals)
        if rule:
            if audit_write.origin.__name__ == "_write":
                new_values = get_new_values(self)
            else:
                new_values = self.sudo().read(load="_classic_write")
            if new_values:
                keys = new_values[0].keys()
                for key in keys:
                    if (
                        str(type(new_values[0][key]))
                        == "<class 'markupsafe.Markup'>"
                    ):
                        new_values[0][key] = str(new_values[0][key])
                        old_values[0][key] = str(old_values[0][key])
                update_type_defaultdict(new_values[0])
                update_type_defaultdict(old_values[0])
                rule.log("write", old_values, new_values)
        return result

    def audit_unlink(self):  # noqa: CCR001
        rule = self._get_audit_rule("unlink")
        if rule:
            old_values = self.read(load="_classic_write")
            if old_values:
                keys = old_values[0].keys()
                for key in keys:
                    if (
                        str(type(old_values[0][key]))
                        == "<class 'markupsafe.Markup'>"
                    ):
                        old_values[0][key] = str(old_values[0][key])
                update_type_defaultdict(old_values[0])
                rule.log("unlink", old_values)
        return audit_unlink.origin(self)

    if "create" in method:
        return audit_create
    if "write" in method:
        return audit_write
    if "unlink" in method:
        return audit_unlink
