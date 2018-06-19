# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class AnsibleDeploymentRule(models.Model):
    _name = 'ansible.deployment.rule'
    _description = 'Ansible Deployment Rule'
    _rec_name = 'build_result'

    active = fields.Boolean(default=True)
    branch_id = fields.Many2one(
        'scm.repository.branch', 'Branch', required=True, ondelete='cascade')
    build_result = fields.Selection([
        ('stable', 'stable'),
        ('unstable', 'stable or unstable'),
    ], required=True, default='stable')
    inventory_type_id = fields.Many2one(
        'ansible.inventory.type', 'Environment', required=True)
    date_planned = fields.Text("Planned date")

    @api.one
    @api.constrains('date_planned')
    def _check_date_planned(self):
        try:
            self.compute_date_planned()
        except Exception as e:
            raise ValidationError(
                _("Planned date is invalid\n\n%s\n\n"
                  "You must specify a dictionary whose "
                  "keys match relativedelta's arguments") % e)

    @api.multi
    def compute_date_planned(self):
        self.ensure_one()
        if not self.date_planned:
            return False
        kwargs = {'second': 0, 'microsecond': 0}
        kwargs.update(safe_eval(self.date_planned))
        date_planned = fields.Datetime.from_string(fields.Datetime.now()) + \
            relativedelta(**kwargs)
        return fields.Datetime.to_string(date_planned)
