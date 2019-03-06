# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools, SUPERUSER_ID


class IrRule(models.AbstractModel):
    _inherit = 'ir.rule'

    error_message = fields.Char(translate=True)

    @api.model
    @tools.ormcache('self._uid', 'model_name', 'mode')
    def _get_rules_to_apply(self, model_name, mode="read"):
        if mode not in self._MODES:
            raise ValueError('Invalid mode: %r' % (mode,))

        if self._uid == SUPERUSER_ID:
            return None

        query = """
        SELECT r.id FROM ir_rule r JOIN ir_model m ON (r.model_id=m.id)
        WHERE m.model=%s AND r.active AND r.perm_{mode}
        AND (r.id IN (
                SELECT rule_group_id FROM rule_group_rel rg
                JOIN res_groups_users_rel gu ON (rg.group_id=gu.gid)
                WHERE gu.uid=%s)
            OR r.global)
        """.format(mode=mode)
        self._cr.execute(query, (model_name, self._uid))
        return [row[0] for row in self._cr.fetchall()]
